from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.scoring import (
    calculate_aggregate_metrics,
    calculate_case_passed,
    calculate_fallback_correct,
    calculate_page_hit,
    calculate_readiness_correct,
    score_expected_keywords,
)
from eval.validate_dataset import (
    DatasetValidationError,
    load_dataset,
    validate_records,
)

ASK_ENDPOINT = "/api/v1/documents/ask"
HEALTH_ENDPOINT = "/api/v1/health"
DEFAULT_DATASET_PATH = Path("eval/questions.jsonl")
DEFAULT_OUTPUT_DIR = Path("eval/results")
MAX_ERROR_MESSAGE_LENGTH = 500
SENSITIVE_ERROR_PATTERN = re.compile(
    r"api[_-]?key|groq_api_key|openai_api_key|evidence[_ -]?text|"
    r"system[_ -]?prompt|user[_ -]?prompt|provider[_ -]?payload",
    flags=re.IGNORECASE,
)
REQUIRED_RESPONSE_FIELDS = {
    "question",
    "answer",
    "answer_ready",
    "evidence_status",
    "confidence_score",
    "citation_count",
    "citations",
    "llm_provider",
    "model_name",
    "fallback_used",
}
RESULT_FIELDS = [
    "id",
    "question",
    "category",
    "difficulty",
    "evaluation_focus",
    "should_answer",
    "answer_ready",
    "readiness_correct",
    "evidence_status",
    "confidence_score",
    "expected_pages",
    "retrieved_pages",
    "page_hit",
    "expected_answer_keywords",
    "matched_keywords",
    "missing_keywords",
    "keyword_match_score",
    "answer",
    "fallback_used",
    "fallback_correct",
    "citation_count",
    "retrieved_filenames",
    "citation_scores",
    "top_citation_score",
    "average_citation_score",
    "duplicate_citation_count",
    "latency_ms",
    "llm_provider",
    "model_name",
    "case_passed",
    "error_type",
    "error_message",
]
CSV_LIST_FIELDS = {
    "evaluation_focus",
    "expected_pages",
    "retrieved_pages",
    "expected_answer_keywords",
    "matched_keywords",
    "missing_keywords",
    "retrieved_filenames",
    "citation_scores",
}


class EvaluationRunnerError(RuntimeError):
    """Base error for expected evaluation-runner failures."""


class BackendUnavailableError(EvaluationRunnerError):
    """Raised when the required backend health check cannot complete."""


class EvaluationRequestError(EvaluationRunnerError):
    def __init__(self, error_type: str, message: str) -> None:
        self.error_type = error_type
        super().__init__(message)


class ResultWritingError(EvaluationRunnerError):
    """Raised when result artifacts cannot be written atomically."""


def _positive_int(value: str) -> int:
    parsed_value = int(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed_value


def _positive_float(value: str) -> float:
    parsed_value = float(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed_value


def _base_url(value: str) -> str:
    normalized = value.rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("base URL must be an HTTP(S) URL")
    if parsed.username or parsed.password:
        raise argparse.ArgumentTypeError("base URL cannot contain credentials")
    return normalized


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate PolicyGPT against the verified RAG benchmark.",
    )
    parser.add_argument(
        "--base-url",
        type=_base_url,
        default="http://localhost:8000",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--top-k", type=_positive_int, default=5)
    parser.add_argument("--timeout", type=_positive_float, default=60.0)

    selection_group = parser.add_mutually_exclusive_group()
    selection_group.add_argument("--limit", type=_positive_int)
    selection_group.add_argument("--question-id")

    parser.add_argument("--fail-on-request-error", action="store_true")
    parser.add_argument("--skip-health-check", action="store_true")
    return parser


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitize_error_message(message: str) -> str:
    sanitized = " ".join(message.split()).strip()
    if SENSITIVE_ERROR_PATTERN.search(sanitized):
        return "[redacted sensitive error message]"
    return sanitized[:MAX_ERROR_MESSAGE_LENGTH]


def _response_json_object(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise EvaluationRequestError(
            "InvalidJSONResponse",
            "Backend returned an invalid JSON response.",
        ) from exc

    if not isinstance(payload, dict):
        raise EvaluationRequestError(
            "InvalidResponseFormat",
            "Backend response must be a JSON object.",
        )

    return payload


def check_backend_health(
    session: requests.Session,
    base_url: str,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url}{HEALTH_ENDPOINT}"
    started_at = time.perf_counter()

    try:
        response = session.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise BackendUnavailableError(
            f"PolicyGPT backend is unavailable at {base_url}."
        ) from exc

    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    if not 200 <= response.status_code < 300:
        raise BackendUnavailableError(
            f"PolicyGPT backend health check returned HTTP "
            f"{response.status_code} at {base_url}."
        )

    try:
        payload = _response_json_object(response)
    except EvaluationRequestError as exc:
        raise BackendUnavailableError(
            f"PolicyGPT backend returned an invalid health response at {base_url}."
        ) from exc

    return {
        "latency_ms": latency_ms,
        "response": payload,
    }


def _validate_api_response(payload: dict[str, Any]) -> dict[str, Any]:
    missing_fields = REQUIRED_RESPONSE_FIELDS - payload.keys()
    if missing_fields:
        raise EvaluationRequestError(
            "MissingResponseFields",
            "Backend response is missing required fields: "
            f"{', '.join(sorted(missing_fields))}.",
        )

    if not isinstance(payload["question"], str):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response question must be a string.",
        )
    if not isinstance(payload["answer"], str):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response answer must be a string.",
        )
    if not isinstance(payload["answer_ready"], bool):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response answer_ready must be boolean.",
        )
    if not isinstance(payload["evidence_status"], str):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response evidence_status must be a string.",
        )

    confidence_score = payload["confidence_score"]
    if isinstance(confidence_score, bool) or not isinstance(
        confidence_score,
        (int, float),
    ) or not math.isfinite(float(confidence_score)):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response confidence_score must be numeric.",
        )

    citation_count = payload["citation_count"]
    if (
        isinstance(citation_count, bool)
        or not isinstance(citation_count, int)
        or citation_count < 0
    ):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response citation_count must be a non-negative integer.",
        )

    citations = payload["citations"]
    if not isinstance(citations, list):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response citations must be a list.",
        )
    if citation_count != len(citations):
        raise EvaluationRequestError(
            "CitationCountMismatch",
            "Response citation_count does not match the citation list.",
        )

    if not isinstance(payload["llm_provider"], str):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response llm_provider must be a string.",
        )
    if payload["model_name"] is not None and not isinstance(
        payload["model_name"],
        str,
    ):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response model_name must be a string or null.",
        )
    if not isinstance(payload["fallback_used"], bool):
        raise EvaluationRequestError(
            "MalformedResponseField",
            "Response fallback_used must be boolean.",
        )

    return payload


def extract_citation_metrics(citations: list[Any]) -> dict[str, Any]:
    retrieved_pages: set[int] = set()
    retrieved_filenames: set[str] = set()
    citation_scores: list[float] = []
    seen_citations: set[tuple[str, int, int, str]] = set()
    duplicate_citation_count = 0

    for index, citation in enumerate(citations, start=1):
        if not isinstance(citation, dict):
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} must be a JSON object.",
            )

        filename = citation.get("filename")
        page_number = citation.get("page_number")
        chunk_index = citation.get("chunk_index")
        excerpt = citation.get("excerpt")
        retrieval_score = citation.get("retrieval_score")

        if not isinstance(filename, str) or not filename:
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} has an invalid filename.",
            )
        if (
            isinstance(page_number, bool)
            or not isinstance(page_number, int)
            or page_number <= 0
        ):
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} has an invalid page_number.",
            )
        if (
            isinstance(chunk_index, bool)
            or not isinstance(chunk_index, int)
            or chunk_index < 0
        ):
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} has an invalid chunk_index.",
            )
        if not isinstance(excerpt, str):
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} has an invalid excerpt.",
            )
        if isinstance(retrieval_score, bool) or not isinstance(
            retrieval_score,
            (int, float),
        ) or not math.isfinite(float(retrieval_score)):
            raise EvaluationRequestError(
                "MalformedCitation",
                f"Citation {index} has an invalid retrieval_score.",
            )

        duplicate_key = (filename, page_number, chunk_index, excerpt)
        if duplicate_key in seen_citations:
            duplicate_citation_count += 1
        else:
            seen_citations.add(duplicate_key)

        retrieved_pages.add(page_number)
        retrieved_filenames.add(filename)
        citation_scores.append(round(float(retrieval_score), 4))

    top_citation_score = max(citation_scores, default=0.0)
    average_citation_score = (
        round(sum(citation_scores) / len(citation_scores), 2)
        if citation_scores
        else 0.0
    )

    return {
        "retrieved_pages": sorted(retrieved_pages),
        "retrieved_filenames": sorted(retrieved_filenames),
        "citation_scores": citation_scores,
        "top_citation_score": round(top_citation_score, 4),
        "average_citation_score": average_citation_score,
        "duplicate_citation_count": duplicate_citation_count,
    }


def _error_result(
    record: dict[str, Any],
    latency_ms: float,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    should_answer = bool(record["should_answer"])
    expected_keywords = list(record["expected_answer_keywords"])

    return {
        "id": record["id"],
        "question": record["question"],
        "category": record["category"],
        "difficulty": record["difficulty"],
        "evaluation_focus": list(record["evaluation_focus"]),
        "should_answer": should_answer,
        "answer_ready": False,
        "readiness_correct": False,
        "evidence_status": "error",
        "confidence_score": 0.0,
        "expected_pages": list(record["expected_pages"]),
        "retrieved_pages": [],
        "page_hit": False if should_answer else None,
        "expected_answer_keywords": expected_keywords,
        "matched_keywords": [],
        "missing_keywords": expected_keywords if should_answer else [],
        "keyword_match_score": 0.0 if should_answer else None,
        "answer": "",
        "fallback_used": False,
        "fallback_correct": None if should_answer else False,
        "citation_count": 0,
        "retrieved_filenames": [],
        "citation_scores": [],
        "top_citation_score": 0.0,
        "average_citation_score": 0.0,
        "duplicate_citation_count": 0,
        "latency_ms": round(max(0.0, latency_ms), 2),
        "llm_provider": "none",
        "model_name": None,
        "case_passed": False,
        "error_type": error_type,
        "error_message": _sanitize_error_message(error_message),
    }


def evaluate_record(
    session: requests.Session,
    record: dict[str, Any],
    base_url: str,
    top_k: int,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url}{ASK_ENDPOINT}"
    started_at = time.perf_counter()

    try:
        response = session.post(
            url,
            json={"question": record["question"], "top_k": top_k},
            timeout=timeout,
        )
        latency_ms = (time.perf_counter() - started_at) * 1000

        if not 200 <= response.status_code < 300:
            raise EvaluationRequestError(
                "HTTPError",
                f"Backend returned HTTP {response.status_code} for {ASK_ENDPOINT}.",
            )

        payload = _validate_api_response(_response_json_object(response))
        citation_metrics = extract_citation_metrics(payload["citations"])
    except requests.Timeout:
        latency_ms = (time.perf_counter() - started_at) * 1000
        return _error_result(
            record,
            latency_ms,
            "Timeout",
            f"Request exceeded the {timeout:g}-second timeout.",
        )
    except requests.ConnectionError:
        latency_ms = (time.perf_counter() - started_at) * 1000
        return _error_result(
            record,
            latency_ms,
            "ConnectionError",
            f"Could not connect to PolicyGPT at {base_url}.",
        )
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - started_at) * 1000
        return _error_result(
            record,
            latency_ms,
            type(exc).__name__,
            "PolicyGPT request failed.",
        )
    except EvaluationRequestError as exc:
        latency_ms = (time.perf_counter() - started_at) * 1000
        return _error_result(
            record,
            latency_ms,
            exc.error_type,
            str(exc),
        )
    except Exception:
        latency_ms = (time.perf_counter() - started_at) * 1000
        return _error_result(
            record,
            latency_ms,
            "ResponseProcessingError",
            "The backend response could not be processed safely.",
        )

    answer = payload["answer"]
    should_answer = bool(record["should_answer"])
    answer_ready = payload["answer_ready"]
    citation_count = payload["citation_count"]
    fallback_used = payload["fallback_used"]
    matched_keywords, missing_keywords, keyword_match_score = (
        score_expected_keywords(answer, list(record["expected_answer_keywords"]))
    )
    page_hit = calculate_page_hit(
        should_answer,
        list(record["expected_pages"]),
        citation_metrics["retrieved_pages"],
    )
    readiness_correct = calculate_readiness_correct(
        should_answer,
        answer_ready,
    )
    fallback_correct = calculate_fallback_correct(
        should_answer,
        answer_ready,
        fallback_used,
        citation_count,
    )
    case_passed = calculate_case_passed(
        should_answer=should_answer,
        answer_ready=answer_ready,
        readiness_correct=readiness_correct,
        page_hit=page_hit,
        keyword_match_score=keyword_match_score,
        fallback_used=fallback_used,
        citation_count=citation_count,
        has_error=False,
    )

    return {
        "id": record["id"],
        "question": record["question"],
        "category": record["category"],
        "difficulty": record["difficulty"],
        "evaluation_focus": list(record["evaluation_focus"]),
        "should_answer": should_answer,
        "answer_ready": answer_ready,
        "readiness_correct": readiness_correct,
        "evidence_status": payload["evidence_status"],
        "confidence_score": round(float(payload["confidence_score"]), 4),
        "expected_pages": list(record["expected_pages"]),
        "retrieved_pages": citation_metrics["retrieved_pages"],
        "page_hit": page_hit,
        "expected_answer_keywords": list(record["expected_answer_keywords"]),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "keyword_match_score": keyword_match_score,
        "answer": answer,
        "fallback_used": fallback_used,
        "fallback_correct": fallback_correct,
        "citation_count": citation_count,
        "retrieved_filenames": citation_metrics["retrieved_filenames"],
        "citation_scores": citation_metrics["citation_scores"],
        "top_citation_score": citation_metrics["top_citation_score"],
        "average_citation_score": citation_metrics["average_citation_score"],
        "duplicate_citation_count": citation_metrics[
            "duplicate_citation_count"
        ],
        "latency_ms": round(max(0.0, latency_ms), 2),
        "llm_provider": payload["llm_provider"],
        "model_name": payload["model_name"],
        "case_passed": case_passed,
        "error_type": None,
        "error_message": None,
    }


def _select_records(
    records: list[dict[str, Any]],
    question_id: str | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    if question_id is not None:
        matching_records = [
            record for record in records if record["id"] == question_id
        ]
        if not matching_records:
            raise EvaluationRunnerError(
                f"Question ID was not found in the dataset: {question_id}"
            )
        return matching_records

    if limit is not None:
        return records[:limit]

    return records


def _dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write_text(path: Path, content: str) -> None:
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_text(content, encoding="utf-8")
        temporary_path.replace(path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise ResultWritingError(f"Failed to write evaluation result: {path}") from exc


def write_json_results(path: Path, payload: dict[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(path, content)


def write_csv_results(path: Path, results: list[dict[str, Any]]) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=RESULT_FIELDS)
    writer.writeheader()

    for result in results:
        row = dict(result)
        for field_name in CSV_LIST_FIELDS:
            row[field_name] = json.dumps(
                row[field_name],
                ensure_ascii=False,
                separators=(",", ":"),
            )
        writer.writerow(row)

    _atomic_write_text(path, output.getvalue())


def run_evaluation(
    args: argparse.Namespace,
    session: requests.Session | None = None,
) -> tuple[dict[str, Any], Path, Path]:
    dataset_path = Path(args.dataset)
    records = load_dataset(dataset_path)
    validate_records(records)
    selected_records = _select_records(records, args.question_id, args.limit)

    created_session = session is None
    active_session = session or requests.Session()
    started_at_utc = _utc_timestamp()
    started_at = time.perf_counter()

    try:
        backend_health = (
            {"skipped": True}
            if args.skip_health_check
            else check_backend_health(
                active_session,
                args.base_url,
                args.timeout,
            )
        )

        results: list[dict[str, Any]] = []
        for record in selected_records:
            result = evaluate_record(
                active_session,
                record,
                args.base_url,
                args.top_k,
                args.timeout,
            )
            results.append(result)

            if args.fail_on_request_error and result["error_type"]:
                raise EvaluationRequestError(
                    str(result["error_type"]),
                    f"Evaluation stopped after request error for {record['id']}: "
                    f"{result['error_message']}",
                )
    finally:
        if created_session:
            active_session.close()

    completed_at_utc = _utc_timestamp()
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    duplicate_citation_warning = any(
        result["duplicate_citation_count"] > 0 for result in results
    )
    summary = calculate_aggregate_metrics(results)
    payload = {
        "run": {
            "run_id": str(uuid4()),
            "started_at_utc": started_at_utc,
            "completed_at_utc": completed_at_utc,
            "duration_ms": duration_ms,
            "base_url": args.base_url,
            "endpoint": ASK_ENDPOINT,
            "dataset_path": str(dataset_path),
            "dataset_sha256": _dataset_sha256(dataset_path),
            "top_k": args.top_k,
            "timeout_seconds": args.timeout,
            "question_count": len(selected_records),
            "backend_health": backend_health,
            "duplicate_citation_warning": duplicate_citation_warning,
        },
        "summary": summary,
        "results": results,
    }

    output_dir = Path(args.output_dir)
    json_path = output_dir / "latest_eval_results.json"
    csv_path = output_dir / "latest_eval_results.csv"
    write_json_results(json_path, payload)
    write_csv_results(csv_path, results)
    return payload, json_path, csv_path


def print_console_summary(
    payload: dict[str, Any],
    json_path: Path,
    csv_path: Path,
) -> None:
    run = payload["run"]
    summary = payload["summary"]

    print("PolicyGPT RAG Evaluation Complete")
    print(f"Run ID: {run['run_id']}")
    print(f"Questions: {summary['total_questions']}")
    print(f"Supported: {summary['supported_questions']}")
    print(f"Unsupported: {summary['unsupported_questions']}")
    print(f"Passed: {summary['passed_questions']}")
    print(f"Failed: {summary['failed_questions_count']}")
    print(f"Request errors: {summary['request_error_count']}")
    print()
    print(
        "Answer readiness accuracy: "
        f"{summary['answer_readiness_accuracy']:.2%}"
    )
    print(f"Fallback accuracy: {summary['fallback_accuracy']:.2%}")
    print(
        "Retrieval page hit rate: "
        f"{summary['retrieval_page_hit_rate']:.2%}"
    )
    print(f"Keyword match rate: {summary['keyword_match_rate']:.2%}")
    print(f"Average confidence: {summary['average_confidence']:.4f}")
    print(
        "Average supported confidence: "
        f"{summary['average_supported_confidence']:.4f}"
    )
    print(f"Average latency: {summary['average_latency_ms']:.2f} ms")
    print(f"Average citations: {summary['average_citation_count']:.2f}")
    if run["duplicate_citation_warning"]:
        print()
        print(
            "Warning: suspicious duplicate citations were detected. "
            "Reset and index the sample PDF once before comparing metrics."
        )
    print()
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        payload, json_path, csv_path = run_evaluation(args)
    except DatasetValidationError as exc:
        print("Dataset validation failed:", file=sys.stderr)
        for error in exc.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    except BackendUnavailableError as exc:
        print(str(exc), file=sys.stderr)
        print("Start it with:", file=sys.stderr)
        print(
            "python -m uvicorn app.api.main:app --reload --reload-dir app "
            "--host 0.0.0.0 --port 8000",
            file=sys.stderr,
        )
        return 1
    except EvaluationRequestError as exc:
        print(_sanitize_error_message(str(exc)), file=sys.stderr)
        return 1
    except EvaluationRunnerError as exc:
        print(_sanitize_error_message(str(exc)), file=sys.stderr)
        return 1
    except OSError as exc:
        print(
            _sanitize_error_message(f"Evaluation file operation failed: {exc}"),
            file=sys.stderr,
        )
        return 1

    print_console_summary(payload, json_path, csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
