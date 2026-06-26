from fastapi import APIRouter, File, UploadFile
import structlog

from app.schemas.document import DocumentExtractionResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

logger = structlog.get_logger(__name__)
document_service = DocumentService()


@router.post("/upload", response_model=DocumentExtractionResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentExtractionResponse:
    """
    Upload a policy PDF, validate it, extract text, clean text,
    and create citation-ready chunks.
    """

    result = await document_service.process_pdf_upload(file)

    logger.info(
        "document_processed",
        document_id=result.document_id,
        filename=result.filename,
        size_bytes=result.size_bytes,
        page_count=result.page_count,
        total_characters=result.total_characters,
        chunk_count=result.chunk_count,
        is_text_extractable=result.is_text_extractable,
    )

    return result