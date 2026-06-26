from fastapi import APIRouter, File, UploadFile
import structlog

from app.schemas.document import DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

logger = structlog.get_logger(__name__)
document_service = DocumentService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload and validate a policy PDF.

    Phase 1 Step 2 scope:
    - Accept PDF upload
    - Validate filename
    - Validate extension
    - Validate content type
    - Validate file size
    - Return upload metadata

    Not included yet:
    - File storage
    - PDF text extraction
    - Chunking
    - Embeddings
    - Vector search
    - LLM answering
    """

    result = await document_service.validate_pdf_upload(file)

    logger.info(
        "document_upload_validated",
        document_id=result.document_id,
        filename=result.filename,
        size_bytes=result.size_bytes,
        content_type=result.content_type,
    )

    return result