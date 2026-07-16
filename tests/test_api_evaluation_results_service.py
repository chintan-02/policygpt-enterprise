from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.evaluation_results_service import (
    EvaluationArtifactInvalidError,
    EvaluationArtifactNotFoundError,
    EvaluationResultsService,
)


def evaluation_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "remote_work_001",
        "question": "What is the equipment allowance?",
        "category": "remote_work",
        "difficulty": "easy",
        "evaluation_focus": ["retrieval"],
        "should_answer": True,
        "answer_ready": True,
        "readiness_correct": True,
        "evidence_status": "strong",
        "confidence_score": 0.8,
        "expected_pages": [5],
        "retrieved_pages": [5],
        "page_hit": True,
        "expected_answer_keywords": ["CAD 300"],
        "matched_keywords": ["CAD 300"],
        "missing_keywords": [],
        "keyword_match_score": 1.0,
        "answer": "The allowance is CAD 300.",
        "fallback_used": False,
        "fallback_correct": None,
        "citation_count": 1,
        "retrieved_filenames": ["sample.pdf"],
        "citation_scores": [0.7],
        "top_citation_score": 0.7,
        "average_citation_score": 0.7,
        "duplicate_citation_count": 0,
        "latency_ms": 100.0,
        "llm_provider": "groq",
        "model_name": "test-model",
        "case_passed": True,
        "error_type": None,
        "error_message": None,
    }
    case.update(overrides)
    return case


def evaluation_payload(
    cases: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    cases = cases or [evaluation_case()]
    total = len(cases)
    supported = sum(case["should_answer"] is True for case in cases)
    passed = sum(case["case_passed"] is True for case in cases)
    return {
        "run": {
            "run_id": "run-123",
            "started_at_utc": "2026-01-01T00:00:00Z",
            "completed_at_utc": "2026-01-01T00:00:01Z",
            "duration_ms": 1000.0,
            "base_url": "http://localhost:8000",
            "endpoint": "/api/v1/documents/ask",
            "dataset_path": "eval/questions.jsonl",
            "dataset_sha256": "a" * 64,
            "top_k": 5,
            "timeout_seconds": 60.0,
            "request_delay_seconds": 0.0,
            "question_count": total,
            "duplicate_citation_warning": False,
        },
        "summary": {
            "total_questions": total,
            "supported_questions": supported,
            "unsupported_questions": total - supported,
            "passed_questions": passed,
            "failed_questions_count": total - passed,
            "request_error_count": 0,
            "answer_readiness_accuracy": 1.0,
            "fallback_accuracy": 0.0,
            "retrieval_page_hit_rate": 1.0 if supported else 0.0,
            "keyword_match_rate": 1.0 if supported else 0.0,
            "average_confidence": 0.8 if total else 0.0,
            "average_supported_confidence": 0.8 if supported else 0.0,
            "average_latency_ms": 100.0 if total else 0.0,
            "average_citation_count": 1.0 if supported else 0.0,
        },
        "results": cases,
    }


def write_artifact(
    root: Path,
    payload: dict[str, object] | None = None,
) -> Path:
    path = root / "eval" / "results" / "latest_eval_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload or evaluation_payload()), encoding="utf-8")
    return path


def write_dataset(root: Path, count: int) -> None:
    path = root / "eval" / "questions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join("{}" for _ in range(count)), encoding="utf-8")


def service(root: Path) -> EvaluationResultsService:
    return EvaluationResultsService(
        "eval/results/latest_eval_results.json",
        repository_root=root,
    )


def test_loads_valid_json_artifact(tmp_path: Path) -> None:
    write_artifact(tmp_path)
    loaded = service(tmp_path).load_latest()
    assert loaded.run.run_id == "run-123"
    assert loaded.summary.total_questions == 1
    assert loaded.results[0].id == "remote_work_001"
    assert loaded.run.backend_base_label == "Local backend"


def test_reads_valid_csv_artifact(tmp_path: Path) -> None:
    json_path = write_artifact(tmp_path)
    csv_path = json_path.with_suffix(".csv")
    csv_path.write_bytes(b"id,case_passed\nremote_work_001,True\n")
    assert service(tmp_path).read_latest_csv() == csv_path.read_bytes()


def test_missing_json_is_not_found(tmp_path: Path) -> None:
    with pytest.raises(EvaluationArtifactNotFoundError):
        service(tmp_path).load_latest()


def test_missing_csv_is_not_found(tmp_path: Path) -> None:
    write_artifact(tmp_path)
    with pytest.raises(EvaluationArtifactNotFoundError):
        service(tmp_path).read_latest_csv()


@pytest.mark.parametrize("content", ["", "{invalid"])
def test_empty_or_invalid_json_is_invalid(tmp_path: Path, content: str) -> None:
    path = write_artifact(tmp_path)
    path.write_text(content, encoding="utf-8")
    with pytest.raises(EvaluationArtifactInvalidError):
        service(tmp_path).load_latest()


@pytest.mark.parametrize("field", ["run", "summary", "results"])
def test_missing_top_level_field_is_invalid(tmp_path: Path, field: str) -> None:
    payload = evaluation_payload()
    payload.pop(field)
    write_artifact(tmp_path, payload)
    with pytest.raises(EvaluationArtifactInvalidError):
        service(tmp_path).load_latest()


def test_malformed_run_metadata_is_invalid(tmp_path: Path) -> None:
    payload = evaluation_payload()
    payload["run"] = {"run_id": "run-123", "question_count": "one"}
    write_artifact(tmp_path, payload)
    with pytest.raises(EvaluationArtifactInvalidError):
        service(tmp_path).load_latest()


def test_malformed_summary_is_invalid(tmp_path: Path) -> None:
    payload = evaluation_payload()
    payload["summary"] = {"total_questions": "one"}
    write_artifact(tmp_path, payload)
    with pytest.raises(EvaluationArtifactInvalidError):
        service(tmp_path).load_latest()


def test_malformed_result_item_is_invalid(tmp_path: Path) -> None:
    payload = evaluation_payload()
    payload["results"] = ["not-an-object"]
    write_artifact(tmp_path, payload)
    with pytest.raises(EvaluationArtifactInvalidError):
        service(tmp_path).load_latest()


def test_step_13_optional_fields_may_be_absent(tmp_path: Path) -> None:
    case = evaluation_case()
    for field in (
        "confidence_breakdown",
        "answerability_score",
        "numeric_mismatch",
        "scope_risk",
        "direct_support",
        "decision_reasons",
    ):
        case.pop(field, None)
    write_artifact(tmp_path, evaluation_payload([case]))
    loaded = service(tmp_path).load_latest().results[0]
    assert loaded.confidence_breakdown is None
    assert loaded.answerability_score is None
    assert loaded.numeric_mismatch is False


def test_future_and_sensitive_unknown_fields_are_not_exposed(tmp_path: Path) -> None:
    payload = evaluation_payload([evaluation_case(api_key="secret")])
    payload["future_field"] = {"authorization": "secret"}
    write_artifact(tmp_path, payload)
    serialized = service(tmp_path).load_latest().model_dump_json()
    assert "future_field" not in serialized
    assert "api_key" not in serialized
    assert "secret" not in serialized


def test_artifact_timestamp_is_timezone_aware(tmp_path: Path) -> None:
    write_artifact(tmp_path)
    timestamp = service(tmp_path).load_latest().artifact.updated_at
    assert timestamp.tzinfo is not None


def test_partial_and_full_run_detection(tmp_path: Path) -> None:
    write_dataset(tmp_path, 2)
    write_artifact(tmp_path)
    assert service(tmp_path).load_latest().artifact.is_partial is True

    cases = [evaluation_case(), evaluation_case(id="remote_work_002")]
    write_artifact(tmp_path, evaluation_payload(cases))
    assert service(tmp_path).load_latest().artifact.is_partial is False


def test_configured_path_accepts_repository_relative_and_rejects_absolute(
    tmp_path: Path,
) -> None:
    configured_path = "eval/results/latest_eval_results.json"
    configured_service = EvaluationResultsService(
        configured_path,
        repository_root=tmp_path,
    )

    assert configured_service.json_path == (tmp_path / configured_path).resolve()
    with pytest.raises(
        EvaluationArtifactInvalidError,
        match="must be repository-relative",
    ):
        EvaluationResultsService(
            "/app/eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )


@pytest.mark.parametrize("configured_path", ["../outside.json", "/tmp/result.json"])
def test_unsafe_paths_are_rejected(tmp_path: Path, configured_path: str) -> None:
    with pytest.raises(EvaluationArtifactInvalidError):
        EvaluationResultsService(configured_path, repository_root=tmp_path)


def test_absolute_run_paths_and_backend_urls_are_not_exposed(tmp_path: Path) -> None:
    payload = evaluation_payload()
    run = payload["run"]
    assert isinstance(run, dict)
    run["dataset_path"] = "/Users/private/eval/questions.jsonl"
    run["base_url"] = "https://private.internal.example"
    write_artifact(tmp_path, payload)
    serialized = service(tmp_path).load_latest().model_dump_json()
    assert "/Users/private" not in serialized
    assert "private.internal.example" not in serialized
    assert "questions.jsonl" in serialized
