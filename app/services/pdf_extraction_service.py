import fitz

from app.core.exceptions import BadRequestException
from app.schemas.document import ExtractedPageText, PDFExtractionResult


class PDFExtractionService:
    """
    Extract text from uploaded PDF files.

    This service keeps page-level metadata because citations later need:
    - document id
    - filename
    - page number
    - extracted text
    """

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> PDFExtractionResult:
        if not pdf_bytes:
            raise BadRequestException("Uploaded PDF file is empty.")

        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            raise BadRequestException(
                "Uploaded file could not be opened as a valid PDF."
            ) from exc

        try:
            pages: list[ExtractedPageText] = []

            for page_index in range(pdf_document.page_count):
                page = pdf_document.load_page(page_index)
                raw_text = page.get_text("text") or ""
                cleaned_text = self._clean_page_text(raw_text)

                pages.append(
                    ExtractedPageText(
                        page_number=page_index + 1,
                        text=cleaned_text,
                        char_count=len(cleaned_text),
                    )
                )

            total_characters = sum(page.char_count for page in pages)

            return PDFExtractionResult(
                page_count=pdf_document.page_count,
                total_characters=total_characters,
                pages=pages,
            )

        finally:
            pdf_document.close()

    def _clean_page_text(self, text: str) -> str:
        """
        Basic PDF text cleanup.

        Keep this light for now. Heavy cleaning should happen later in a
        dedicated text cleaning/chunking step.
        """

        lines = [line.strip() for line in text.splitlines()]
        non_empty_lines = [line for line in lines if line]

        return "\n".join(non_empty_lines)