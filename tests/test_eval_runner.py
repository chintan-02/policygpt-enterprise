import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import requests

from eval.run_eval import (
    BackendUnavailableError,
    EvaluationRequestError,
    build_argument_parser,
    check_backend_health,
    evaluate_record,
    extract_citation_metrics,
    run_evaluation,
)
from eval.validate_dataset import load_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "eval" / "questions.jsonl"


class FakeResponse:
    def __init__(
        self,
        payload: object | None = None,
        *,
        status_code: int = 200,
        json_error: bool = False,
    ) -> None:
        self.payload = payload
        self.status_code = status_code
        self.json_error = json_error

    def json(self) -> object:
        if self.json_error:
            raise ValueError("invalid JSON")
        return self.payload


def _supported_record() -> dict[str, Any]:
    return load_dataset(DATASET_PATH)[0]


def _unsupported_record() -> dict[str, Any]:
    return next(
        record
        for record in load_dataset(DATASET_PATH)
        if record["should_answer"] is False
    )


def _citation(
    *,
    page_number: int = 5,
    filename: str = "sample_hr_policy.pdf",
    chunk_index: int = 1,
    excerpt: str = "Equipment allowance evidence.",
    score: float = 0.8,
) -> dict[str, object]:
    return {
        "document_id": "document-1",
        "filename": filename,
        "page_number": page_number,
        "section_title": "Remote and Hybrid Work",
        "chunk_index": chunk_index,
        "excerpt": excerpt,
        "retrieval_score": score,
    }


def _supported_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "question": _supported_record()["question"],
        "answer": (
            "The one-time allowance is CAD 300. Receipts and approval are "
            "required before reimbursement."
        ),
        "answer_ready": True,
        "evidence_status": "strong",
        "confidence_score": 0.8,
        "citation_count": 1,
        "citations": [_citation()],
        "llm_provider": "groq",
        "model_name": "test-model",
        "fallback_used": False,
    }
    payload.update(overrides)
    return payload


def _unsupported_payload() -> dict[str, object]:
    return {
        "question": _unsupported_record()["question"],
        "answer": "I could not find enough supporting evidence.",
        "answer_ready": False,
        "evidence_status": "insufficient",
        "confidence_score": 0.0,
        "citation_count": 0,
        "citations": [],
        "llm_provider": "none",
        "model_name": None,
        "fallback_used": True,
    }


def _session_with_post(value: object) -> Mock:
    session = Mock(spec=requests.Session)
    if isinstance(value, BaseException):
        session.post.side_effect = value
    else:
        session.post.return_value = value
    return session


def _args(tmp_path: Path, *extra: str) -> argparse.Namespace:
    return build_argument_parser().parse_args(
        [
            "--dataset",
            str(DATASET_PATH),
            "--output-dir",
            str(tmp_path),
            "--skip-health-check",
            *extra,
        ]
    )


def test_health_check_success() -> None:
    session = Mock(spec=requests.Session)
    session.get.return_value = FakeResponse({"status": "healthy"})

    result = check_backend_health(session, "http://localhost:8000", 5.0)

    assert result["response"] == {"status": "healthy"}
    assert result["latency_ms"] >= 0


def test_health_check_unavailable() -> None:
    session = Mock(spec=requests.Session)
    session.get.side_effect = requests.ConnectionError("offline")

    with pytest.raises(BackendUnavailableError, match="unavailable"):
        check_backend_health(session, "http://localhost:8000", 5.0)


def test_successful_supported_answer() -> None:
    result = evaluate_record(
        _session_with_post(FakeResponse(_supported_payload())),
        _supported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["case_passed"] is True
    assert result["page_hit"] is True
    assert result["keyword_match_score"] == 1.0
    assert result["error_type"] is None


def test_successful_unsupported_fallback() -> None:
    result = evaluate_record(
        _session_with_post(FakeResponse(_unsupported_payload())),
        _unsupported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["case_passed"] is True
    assert result["fallback_correct"] is True
    assert result["page_hit"] is None
    assert result["keyword_match_score"] is None


@pytest.mark.parametrize(
    ("failure", "expected_type"),
    [
        (requests.Timeout("slow"), "Timeout"),
        (requests.ConnectionError("offline"), "ConnectionError"),
    ],
)
def test_network_request_failures(
    failure: requests.RequestException,
    expected_type: str,
) -> None:
    result = evaluate_record(
        _session_with_post(failure),
        _supported_record(),
        "http://localhost:8000",
        5,
        1.0,
    )

    assert result["case_passed"] is False
    assert result["error_type"] == expected_type
    assert result["missing_keywords"] == _supported_record()[
        "expected_answer_keywords"
    ]


def test_non_2xx_response() -> None:
    result = evaluate_record(
        _session_with_post(FakeResponse(status_code=503)),
        _supported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["error_type"] == "HTTPError"
    assert "503" in result["error_message"]


def test_invalid_json_response() -> None:
    result = evaluate_record(
        _session_with_post(FakeResponse(json_error=True)),
        _supported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["error_type"] == "InvalidJSONResponse"


def test_missing_response_fields() -> None:
    result = evaluate_record(
        _session_with_post(FakeResponse({"answer": "incomplete"})),
        _supported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["error_type"] == "MissingResponseFields"
    assert result["case_passed"] is False


def test_malformed_citation_object() -> None:
    payload = _supported_payload(citations=[{"filename": "policy.pdf"}])
    result = evaluate_record(
        _session_with_post(FakeResponse(payload)),
        _supported_record(),
        "http://localhost:8000",
        5,
        60.0,
    )

    assert result["error_type"] == "MalformedCitation"


def test_run_continues_after_one_request_error(tmp_path: Path) -> None:
    session = Mock(spec=requests.Session)
    session.post.side_effect = [
        requests.Timeout("slow"),
        FakeResponse(_supported_payload()),
    ]

    payload, _, _ = run_evaluation(_args(tmp_path, "--limit", "2"), session)

    assert len(payload["results"]) == 2
    assert payload["summary"]["request_error_count"] == 1


def test_fail_on_request_error_stops_run(tmp_path: Path) -> None:
    session = _session_with_post(requests.Timeout("slow"))

    with pytest.raises(EvaluationRequestError, match="remote_work_001"):
        run_evaluation(
            _args(
                tmp_path,
                "--limit",
                "1",
                "--fail-on-request-error",
            ),
            session,
        )

    assert not (tmp_path / "latest_eval_results.json").exists()


def test_json_csv_structure_and_dataset_hash(tmp_path: Path) -> None:
    payload, json_path, csv_path = run_evaluation(
        _args(tmp_path, "--limit", "1"),
        _session_with_post(FakeResponse(_supported_payload())),
    )

    saved_payload = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    expected_hash = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    assert set(saved_payload) == {"run", "summary", "results"}
    assert saved_payload["run"]["dataset_sha256"] == expected_hash
    assert payload["run"]["question_count"] == 1
    assert len(rows) == 1
    assert set(rows[0]) == set(payload["results"][0])
    assert json.loads(rows[0]["retrieved_pages"]) == [5]


def test_question_filtering_by_id(tmp_path: Path) -> None:
    payload, _, _ = run_evaluation(
        _args(tmp_path, "--question-id", "remote_work_001"),
        _session_with_post(FakeResponse(_supported_payload())),
    )

    assert [result["id"] for result in payload["results"]] == [
        "remote_work_001"
    ]


def test_limit_behavior(tmp_path: Path) -> None:
    session = Mock(spec=requests.Session)
    session.post.side_effect = [
        FakeResponse(_supported_payload()),
        FakeResponse(_supported_payload()),
        FakeResponse(_supported_payload()),
    ]

    payload, _, _ = run_evaluation(_args(tmp_path, "--limit", "3"), session)

    assert payload["run"]["question_count"] == 3
    assert len(payload["results"]) == 3


def test_limit_and_question_id_are_incompatible() -> None:
    parser = build_argument_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--limit",
                "2",
                "--question-id",
                "remote_work_001",
            ]
        )


def test_unique_sorted_pages_and_duplicate_detection() -> None:
    duplicate = _citation(page_number=5, chunk_index=2, excerpt="Same excerpt")
    metrics = extract_citation_metrics(
        [
            _citation(page_number=8, chunk_index=1),
            duplicate,
            dict(duplicate),
            _citation(page_number=5, chunk_index=3),
        ]
    )

    assert metrics["retrieved_pages"] == [5, 8]
    assert metrics["retrieved_filenames"] == ["sample_hr_policy.pdf"]
    assert metrics["duplicate_citation_count"] == 1


def test_generated_files_do_not_contain_hidden_evidence(tmp_path: Path) -> None:
    citation = _citation()
    citation["evidence_text"] = "private complete evidence"
    payload = _supported_payload(citations=[citation])

    _, json_path, csv_path = run_evaluation(
        _args(tmp_path, "--limit", "1"),
        _session_with_post(FakeResponse(payload)),
    )

    generated_output = (
        json_path.read_text(encoding="utf-8")
        + csv_path.read_text(encoding="utf-8")
    ).lower()
    assert "evidence_text" not in generated_output
    assert "private complete evidence" not in generated_output
