from pathlib import PurePath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestException
from app.schemas.document import DocumentUploadResponse


class DocumentService:
    """
    Service layer for document upload validation.

    This step only validates uploaded PDF files.
    It does not extract text, store files, create chunks, or call embeddings yet.
    """

    allowed_extensions = {".pdf"}
    allowed_content_types = {
        "application/pdf",
        "application/octet-stream",
    }

    async def validate_pdf_upload(self, file: UploadFile) -> DocumentUploadResponse:
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

        size_bytes = await self._calculate_file_size(file)

        if size_bytes == 0:
            raise BadRequestException("Uploaded PDF file is empty.")

        if size_bytes > settings.max_pdf_upload_size_bytes:
            raise BadRequestException(
                f"PDF file is too large. Maximum allowed size is "
                f"{settings.max_pdf_upload_size_mb} MB."
            )

        await file.seek(0)

        return DocumentUploadResponse(
            document_id=str(uuid4()),
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            message="PDF uploaded and validated successfully.",
        )

    async def _calculate_file_size(self, file: UploadFile) -> int:
        """
        Calculate uploaded file size safely in chunks.

        This avoids loading very large files into memory at once.
        """

        await file.seek(0)

        size = 0
        chunk_size = 1024 * 1024

        while chunk := await file.read(chunk_size):
            size += len(chunk)

        await file.seek(0)

        return size