import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.schemas.observability import RAGQueryLogEntry
from app.services.rag_logging_service import RAGLoggingService


def _settings(
    log_path: Path,
    *,
    enabled: bool = True,
    include_question: bool = True,
) -> Settings:
    return Settings(
        _env_file=None,
        DEBUG=False,
        ENABLE_RAG_QUERY_LOGGING=enabled,
        RAG_QUERY_LOG_PATH=str(log_path),
        RAG_LOG_INCLUDE_QUESTION=include_question,
    )


def _entry(**overrides: object) -> RAGQueryLogEntry:
    values: dict[str, object] = {
        "query_id": "query-1",
        "timestamp": datetime.now(timezone.utc),
        "question": "What is the café allowance?",
        "question_length": 27,
        "answer_ready": True,
        "evidence_status": "strong",
        "confidence_score": 0.8,
        "top_retrieval_score": 0.9,
        "average_retrieval_score": 0.7,
        "citation_count": 2,
        "retrieved_pages": [1, 2],
        "retrieved_filenames": ["política.pdf"],
        "llm_provider": "groq",
        "model_name": "test-model",
        "fallback_used": False,
        "latency_ms": 12.5,
        "top_k": 5,
        "min_retrieval_score": 0.45,
        "error_type": None,
        "error_message": None,
    }
    values.update(overrides)
    return RAGQueryLogEntry.model_validate(values)


def _service(settings: Settings) -> RAGLoggingService:
    service = RAGLoggingService.__new__(RAGLoggingService)
    service.settings = settings
    return service


def test_creates_parent_directory_and_writes_valid_unicode_jsonl(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "missing" / "rag_queries.jsonl"
    service = _service(_settings(log_path))

    service.log_query(_entry())

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["question"] == "What is the café allowance?"
    assert record["retrieved_filenames"] == ["política.pdf"]
    assert record["timestamp"].endswith("Z")


def test_writes_exactly_one_record_per_line(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _service(_settings(log_path))

    service.log_query(_entry(query_id="query-1"))
    service.log_query(_entry(query_id="query-2"))

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["query_id"] for line in lines] == [
        "query-1",
        "query-2",
    ]


def test_disabled_logging_does_not_create_a_file(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _service(_settings(log_path, enabled=False))

    service.log_query(_entry())

    assert not log_path.exists()


def test_question_omission_preserves_question_length(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _service(_settings(log_path, include_question=False))

    service.log_query(_entry())

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["question"] is None
    assert record["question_length"] == 27


def test_logging_failure_does_not_raise_into_caller(tmp_path: Path) -> None:
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("occupied", encoding="utf-8")
    service = _service(_settings(parent_file / "rag_queries.jsonl"))

    service.log_query(_entry())


def test_output_omits_sensitive_error_content(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _service(_settings(log_path))
    sensitive_message = (
        "GROQ_API_KEY=top-secret system_prompt=hidden "
        "evidence_text=complete-provider-content"
    )

    service.log_query(
        _entry(
            error_type="Provider Error!",
            error_message=sensitive_message,
            decision_reasons=[
                "The embedding payload included evidence_text content."
            ],
        )
    )

    output = log_path.read_text(encoding="utf-8").lower()
    assert "top-secret" not in output
    assert "groq_api_key" not in output
    assert "system_prompt" not in output
    assert "evidence_text" not in output
    record = json.loads(output)
    assert record["error_type"] == "provider_error_"
    assert record["error_message"] == "[redacted sensitive error message]"
    assert record["decision_reasons"] == [
        "[redacted sensitive error message]"
    ]
