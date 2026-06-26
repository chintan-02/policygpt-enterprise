from pathlib import PurePath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestException
from app.schemas.document import DocumentExtractionResponse
from app.services.pdf_extraction_service import PDFExtractionService


class DocumentService:
    """
    Service layer for document upload validation and text extraction.

    Phase 1 Step 3 scope:
    - validate PDF upload
    - read PDF bytes
    - extract page-level text
    - return extraction metadata

    Not included yet:
    - file storage
    - chunking
    - embeddings
    - vector search
    - LLM answering
    """

    allowed_extensions = {".pdf"}
    allowed_content_types = {
        "application/pdf",
        "application/octet-stream",
    }

    def __init__(self) -> None:
        self.pdf_extraction_service = PDFExtractionService()

    async def process_pdf_upload(self, file: UploadFile) -> DocumentExtractionResponse:
        settings = get_settings()

        filename = file.filename or ""

        if not filename.strip():
            raise BadRequestException("Uploaded file must have a filename.")

        file_extension = PurePath(filename).suffix.lower()

        if file_extension not in self.allowed_extensions:
            raise BadRequestException("Only PDF files are supported.")

        content_type = file.content_type or "unknown"

        if content_type not in self.allowed_content_types:
            raise BadRequestException(
                f"Invalid file content type: {content_type}. Only PDF files are supported."
            )

        pdf_bytes = await file.read()
        await file.seek(0)

        size_bytes = len(pdf_bytes)

        if size_bytes == 0:
            raise BadRequestException("Uploaded PDF file is empty.")

        if size_bytes > settings.max_pdf_upload_size_bytes:
            raise BadRequestException(
                f"PDF file is too large. Maximum allowed size is "
                f"{settings.max_pdf_upload_size_mb} MB."
            )

        document_id = str(uuid4())

        extraction_result = self.pdf_extraction_service.extract_text_from_pdf(pdf_bytes)

        preview_text = self._build_preview_text(
            pages_text=[page.text for page in extraction_result.pages],
            max_characters=1000,
        )

        is_text_extractable = extraction_result.total_characters > 0

        if is_text_extractable:
            message = "PDF uploaded and text extracted successfully."
        else:
            message = (
                "PDF uploaded successfully, but no selectable text was found. "
                "This may be a scanned or image-only PDF."
            )

        return DocumentExtractionResponse(
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            page_count=extraction_result.page_count,
            total_characters=extraction_result.total_characters,
            is_text_extractable=is_text_extractable,
            preview_text=preview_text,
            pages=extraction_result.pages,
            message=message,
        )

    def _build_preview_text(
        self,
        pages_text: list[str],
        max_characters: int = 1000,
    ) -> str:
        combined_text = "\n".join(text for text in pages_text if text).strip()

        if len(combined_text) <= max_characters:
            return combined_text

        return combined_text[:max_characters].strip() + "..."