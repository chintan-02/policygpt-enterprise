import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.core.config import Settings
from app.schemas.document import (
    CitationCard,
    ConfidenceBreakdown,
    DocumentAnswerRequest,
    DocumentEvidenceRequest,
    DocumentEvidenceResponse,
    DocumentSearchResult,
)
from app.services.confidence_service import ConfidenceConfig
from app.services.document_service import DocumentService
from app.services.rag_logging_service import RAGLoggingService
from app.services.retrieval_service import RetrievalService


def _settings(log_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        DEBUG=False,
        ENABLE_RAG_QUERY_LOGGING=True,
        RAG_QUERY_LOG_PATH=str(log_path),
        RAG_LOG_INCLUDE_QUESTION=True,
        MIN_RETRIEVAL_SCORE=0.45,
    )


def _citation(
    *,
    page_number: int,
    filename: str,
    chunk_index: int,
    score: float,
) -> CitationCard:
    return CitationCard(
        document_id=f"document-{chunk_index}",
        filename=filename,
        page_number=page_number,
        section_title="Benefits",
        chunk_index=chunk_index,
        excerpt="Short public excerpt.",
        evidence_text="Complete private evidence that must not be logged.",
        retrieval_score=score,
    )


def _evidence(
    *,
    answer_ready: bool = True,
    citations: list[CitationCard] | None = None,
    top_score: float = 0.88,
    average_score: float = 0.61,
    confidence_breakdown: ConfidenceBreakdown | None = None,
) -> DocumentEvidenceResponse:
    citation_list = citations or []
    return DocumentEvidenceResponse(
        query="What is covered?",
        top_k=7,
        answer_ready=answer_ready,
        evidence_status="strong" if answer_ready else "insufficient",
        confidence_score=0.75 if answer_ready else 0.0,
        top_retrieval_score=top_score,
        average_retrieval_score=average_score,
        min_retrieval_score=0.45,
        confidence_breakdown=confidence_breakdown,
        citation_count=len(citation_list),
        citations=citation_list,
        fallback_message=(
            None if answer_ready else "There is not enough supporting evidence."
        ),
    )


def _document_service(log_path: Path) -> DocumentService:
    settings = _settings(log_path)
    logging_service = RAGLoggingService.__new__(RAGLoggingService)
    logging_service.settings = settings

    service = DocumentService.__new__(DocumentService)
    service.settings = settings
    service.retrieval_service = Mock()
    service.answer_generation_service = Mock()
    service.rag_logging_service = logging_service
    return service


def _records(log_path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]


def test_supported_answer_creates_one_complete_record(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _document_service(log_path)
    citations = [
        _citation(page_number=6, filename="policy-b.pdf", chunk_index=1, score=0.8),
        _citation(page_number=2, filename="policy-a.pdf", chunk_index=2, score=0.7),
        _citation(page_number=6, filename="policy-b.pdf", chunk_index=3, score=0.6),
    ]
    confidence_breakdown = ConfidenceBreakdown(
        answerability_score=0.72,
        top_retrieval_score=0.80,
        average_retrieval_score=0.70,
        retrieval_margin=0.30,
        lexical_coverage=0.85,
        top_chunk_lexical_coverage=0.75,
        numeric_consistency=None,
        numeric_mismatch=False,
        query_numeric_claims=[],
        evidence_numeric_claims=[],
        missing_numeric_claims=[],
        scope_risk=False,
        scope_risk_reason=None,
        matched_query_terms=["cover"],
        missing_query_terms=[],
        direct_support=True,
        decision_reasons=["Direct policy support was found."],
    )
    service.retrieval_service.retrieve_evidence.return_value = _evidence(
        citations=citations,
        confidence_breakdown=confidence_breakdown,
    )
    service.answer_generation_service.generate_answer.return_value = (
        "The policy covers the allowance.",
        "test-model",
        "groq",
        False,
    )

    response = service.answer_question(
        DocumentAnswerRequest(question="What is covered?", top_k=7)
    )

    assert response.answer_ready is True
    records = _records(log_path)
    assert len(records) == 1
    record = records[0]
    assert record["answer_ready"] is True
    assert record["retrieved_pages"] == [2, 6]
    assert record["retrieved_filenames"] == ["policy-a.pdf", "policy-b.pdf"]
    assert record["answerability_score"] == 0.72
    assert record["top_retrieval_score"] == 0.8
    assert record["average_retrieval_score"] == 0.7
    assert record["retrieval_margin"] == 0.3
    assert record["lexical_coverage"] == 0.85
    assert record["top_chunk_lexical_coverage"] == 0.75
    assert record["numeric_mismatch"] is False
    assert record["scope_risk"] is False
    assert record["direct_support"] is True
    assert record["decision_reasons"] == ["Direct policy support was found."]
    assert record["top_k"] == 7
    assert record["min_retrieval_score"] == 0.45
    assert record["latency_ms"] >= 0
    assert "Complete private evidence" not in log_path.read_text(encoding="utf-8")


def test_unsupported_question_creates_one_record_without_calling_llm(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _document_service(log_path)
    service.retrieval_service.retrieve_evidence.return_value = _evidence(
        answer_ready=False,
        top_score=0.31,
        average_score=0.22,
    )

    response = service.answer_question(
        DocumentAnswerRequest(question="Unknown detail?", top_k=4)
    )

    assert response.answer_ready is False
    service.answer_generation_service.generate_answer.assert_not_called()
    records = _records(log_path)
    assert len(records) == 1
    assert records[0]["llm_provider"] == "none"
    assert records[0]["fallback_used"] is True
    assert records[0]["top_retrieval_score"] == 0.31


def test_provider_failure_fallback_creates_exactly_one_record(tmp_path: Path) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _document_service(log_path)
    service.retrieval_service.retrieve_evidence.return_value = _evidence(
        citations=[
            _citation(
                page_number=1,
                filename="policy.pdf",
                chunk_index=1,
                score=0.8,
            )
        ]
    )
    service.answer_generation_service.generate_answer.return_value = (
        "Review the citation evidence.",
        "test-model",
        "groq",
        True,
    )

    response = service.answer_question(
        DocumentAnswerRequest(question="What is covered?", top_k=5)
    )

    assert response.fallback_used is True
    records = _records(log_path)
    assert len(records) == 1
    assert records[0]["llm_provider"] == "groq"
    assert records[0]["model_name"] == "test-model"
    assert records[0]["fallback_used"] is True


def test_unexpected_exception_logs_error_defaults_and_reraises(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "rag_queries.jsonl"
    service = _document_service(log_path)
    service.retrieval_service.retrieve_evidence.side_effect = RuntimeError(
        "embedding unavailable"
    )

    with pytest.raises(RuntimeError, match="embedding unavailable"):
        service.answer_question(
            DocumentAnswerRequest(question="What is covered?", top_k=6)
        )

    records = _records(log_path)
    assert len(records) == 1
    record = records[0]
    assert record["answer_ready"] is False
    assert record["evidence_status"] == "error"
    assert record["confidence_score"] == 0.0
    assert record["top_retrieval_score"] == 0.0
    assert record["average_retrieval_score"] == 0.0
    assert record["citation_count"] == 0
    assert record["retrieved_pages"] == []
    assert record["retrieved_filenames"] == []
    assert record["llm_provider"] == "none"
    assert record["model_name"] is None
    assert record["fallback_used"] is True
    assert record["error_type"] == "RuntimeError"
    assert record["error_message"] == "[redacted sensitive error message]"


def test_retrieval_metrics_use_raw_results_before_filtering(tmp_path: Path) -> None:
    service = RetrievalService.__new__(RetrievalService)
    service.settings = _settings(tmp_path / "unused.jsonl")
    service.confidence_config = ConfidenceConfig()
    service.embedding_service = Mock()
    service.embedding_service.embed_query.return_value = [0.1, 0.2]
    service.vector_store_service = Mock()
    service.vector_store_service.search_similar_chunks.return_value = [
        DocumentSearchResult(
            document_id="document-1",
            filename="policy.pdf",
            page_number=1,
            chunk_index=1,
            text="Relevant covered policy evidence.",
            char_count=33,
            score=0.8,
        ),
        DocumentSearchResult(
            document_id="document-2",
            filename="policy.pdf",
            page_number=2,
            chunk_index=2,
            text="Below threshold evidence.",
            char_count=25,
            score=0.2,
        ),
    ]

    evidence_request = DocumentEvidenceRequest(query="What is covered?", top_k=2)
    response = service.retrieve_evidence(evidence_request)

    assert evidence_request.top_k == 2
    assert response.citation_count == 1
    assert response.top_retrieval_score == 0.8
    assert response.average_retrieval_score == 0.5
