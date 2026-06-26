from pathlib import PurePath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestException
from app.schemas.document import DocumentExtractionResponse, ExtractedPageText
from app.services.chunking_service import ChunkingService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.text_cleaning_service import TextCleaningService


class DocumentService:
    """
    Service layer for document upload, text extraction, cleaning, and chunking.

    Phase 1 Step 4 scope:
    - validate PDF upload
    - extract page-level text
    - clean extracted text
    - create citation-ready chunks with metadata

    Not included yet:
    - file storage
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
        self.text_cleaning_service = TextCleaningService()
        self.chunking_service = ChunkingService()

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

        cleaned_pages, page_section_titles = self._clean_extracted_pages(
            pages=extraction_result.pages,
        )

        total_characters = sum(page.char_count for page in cleaned_pages)
        is_text_extractable = total_characters > 0

        chunks = self.chunking_service.create_chunks(
            document_id=document_id,
            filename=filename,
            pages=cleaned_pages,
            page_section_titles=page_section_titles,
            chunk_size_chars=settings.text_chunk_size_chars,
            chunk_overlap_chars=settings.text_chunk_overlap_chars,
        )

        preview_text = self._build_preview_text(
            pages_text=[page.text for page in cleaned_pages],
            max_characters=1000,
        )

        if is_text_extractable:
            message = "PDF uploaded, text cleaned, and chunks created successfully."
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
            total_characters=total_characters,
            is_text_extractable=is_text_extractable,
            preview_text=preview_text,
            chunk_count=len(chunks),
            pages=cleaned_pages,
            chunks=chunks,
            message=message,
        )

    def _clean_extracted_pages(
        self,
        pages: list[ExtractedPageText],
    ) -> tuple[list[ExtractedPageText], dict[int, str | None]]:
        cleaned_pages: list[ExtractedPageText] = []
        page_section_titles: dict[int, str | None] = {}

        for page in pages:
            cleaned_text = self.text_cleaning_service.clean_page_text(page.text)

            page_section_titles[page.page_number] = (
                self.text_cleaning_service.infer_section_title(
                    original_text=page.text,
                    fallback=f"Page {page.page_number}",
                )
            )

            cleaned_pages.append(
                ExtractedPageText(
                    page_number=page.page_number,
                    text=cleaned_text,
                    char_count=len(cleaned_text),
                )
            )

        return cleaned_pages, page_section_titles

    def _build_preview_text(
        self,
        pages_text: list[str],
        max_characters: int = 1000,
    ) -> str:
        combined_text = " ".join(text for text in pages_text if text).strip()

        if len(combined_text) <= max_characters:
            return combined_text

        return combined_text[:max_characters].strip() + "..."