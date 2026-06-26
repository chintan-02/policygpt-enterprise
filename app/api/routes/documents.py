from fastapi import APIRouter, File, UploadFile
import structlog

from app.schemas.document import (
    DocumentAnswerRequest,
    DocumentAnswerResponse,
    DocumentEvidenceRequest,
    DocumentEvidenceResponse,
    DocumentIngestionResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

logger = structlog.get_logger(__name__)
document_service = DocumentService()


@router.post("/upload", response_model=DocumentIngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentIngestionResponse:
    result = await document_service.process_pdf_upload(file)

    logger.info(
        "document_ingested",
        document_id=result.document_id,
        filename=result.filename,
        size_bytes=result.size_bytes,
        page_count=result.page_count,
        total_characters=result.total_characters,
        chunk_count=result.chunk_count,
        stored_chunk_count=result.stored_chunk_count,
        collection_name=result.collection_name,
        is_text_extractable=result.is_text_extractable,
    )

    return result


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
) -> DocumentSearchResponse:
    result = document_service.search_documents(search_request)

    logger.info(
        "document_search_completed",
        query=search_request.query,
        top_k=search_request.top_k,
        result_count=result.result_count,
    )

    return result


@router.post("/evidence", response_model=DocumentEvidenceResponse)
async def retrieve_document_evidence(
    evidence_request: DocumentEvidenceRequest,
) -> DocumentEvidenceResponse:
    result = document_service.retrieve_evidence(evidence_request)

    logger.info(
        "document_evidence_retrieved",
        query=evidence_request.query,
        top_k=evidence_request.top_k,
        citation_count=result.citation_count,
        evidence_status=result.evidence_status,
        confidence_score=result.confidence_score,
        answer_ready=result.answer_ready,
    )

    return result


@router.post("/ask", response_model=DocumentAnswerResponse)
async def ask_document_question(
    answer_request: DocumentAnswerRequest,
) -> DocumentAnswerResponse:
    result = document_service.answer_question(answer_request)

    logger.info(
        "document_answer_generated",
        question=answer_request.question,
        top_k=answer_request.top_k,
        answer_ready=result.answer_ready,
        evidence_status=result.evidence_status,
        confidence_score=result.confidence_score,
        citation_count=result.citation_count,
        fallback_used=result.fallback_used,
        llm_provider=result.llm_provider,
        model_name=result.model_name,
    )

    return result