from fastapi import APIRouter, File, UploadFile
import structlog

from app.schemas.document import (
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
    """
    Upload a policy PDF, validate it, extract text, clean text,
    create chunks, generate embeddings, and store chunks in ChromaDB.
    """

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


@router.post("/upload", response_model=DocumentIngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentIngestionResponse:
    """
    Raw semantic search endpoint.

    Useful for debugging retrieval quality.
    """

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
    """
    Retrieve citation-ready evidence cards.

    This endpoint prepares evidence for future LLM answer generation.
    It does not generate the final answer yet.
    """

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