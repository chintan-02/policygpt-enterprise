from app.core.exceptions import ConfigurationException
from app.schemas.document import DocumentChunk, ExtractedPageText


class ChunkingService:
    """
    Create page-aware text chunks.

    Important:
    Chunks should not blindly lose page metadata.
    Citation-based RAG depends on knowing where each chunk came from.
    """

    def create_chunks(
        self,
        document_id: str,
        filename: str,
        pages: list[ExtractedPageText],
        page_section_titles: dict[int, str | None],
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[DocumentChunk]:
        self._validate_chunk_settings(
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        )

        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for page in pages:
            page_text = page.text.strip()

            if not page_text:
                continue

            page_chunks = self._split_text(
                text=page_text,
                chunk_size_chars=chunk_size_chars,
                chunk_overlap_chars=chunk_overlap_chars,
            )

            for chunk_text in page_chunks:
                chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        filename=filename,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        section_title=page_section_titles.get(page.page_number),
                        text=chunk_text,
                        char_count=len(chunk_text),
                    )
                )

                chunk_index += 1

        return chunks

    def _split_text(
        self,
        text: str,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[str]:
        """
        Split text using character windows with overlap.

        This is simple and reliable for Phase 1.
        Later, we can upgrade to token-aware or sentence-aware chunking.
        """

        text = text.strip()

        if not text:
            return []

        if len(text) <= chunk_size_chars:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + chunk_size_chars
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = end - chunk_overlap_chars

        return chunks

    def _validate_chunk_settings(
        self,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> None:
        if chunk_size_chars <= 0:
            raise ConfigurationException("TEXT_CHUNK_SIZE_CHARS must be greater than 0.")

        if chunk_overlap_chars < 0:
            raise ConfigurationException(
                "TEXT_CHUNK_OVERLAP_CHARS cannot be negative."
            )

        if chunk_overlap_chars >= chunk_size_chars:
            raise ConfigurationException(
                "TEXT_CHUNK_OVERLAP_CHARS must be smaller than TEXT_CHUNK_SIZE_CHARS."
            )