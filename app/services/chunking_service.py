import re

from app.core.exceptions import ConfigurationException
from app.schemas.document import DocumentChunk, ExtractedPageText


class ChunkingService:
    """
    Create page-aware text chunks.

    Citation-based RAG depends on knowing where each chunk came from.
    This version avoids splitting in the middle of words when possible.
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
        text = text.strip()

        if not text:
            return []

        if len(text) <= chunk_size_chars:
            return [text]

        sentences = self._split_into_sentences(text)

        chunks: list[str] = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            if not current_chunk:
                current_chunk = sentence
                continue

            candidate = f"{current_chunk} {sentence}".strip()

            if len(candidate) <= chunk_size_chars:
                current_chunk = candidate
                continue

            chunks.extend(
                self._finalize_chunk(
                    text=current_chunk,
                    chunk_size_chars=chunk_size_chars,
                    chunk_overlap_chars=chunk_overlap_chars,
                )
            )

            overlap_text = self._get_overlap_text(
                text=chunks[-1],
                chunk_overlap_chars=chunk_overlap_chars,
            )

            current_chunk = f"{overlap_text} {sentence}".strip()

            while len(current_chunk) > chunk_size_chars:
                split_at = self._find_split_position(
                    text=current_chunk,
                    max_chars=chunk_size_chars,
                )

                chunk = current_chunk[:split_at].strip()

                if chunk:
                    chunks.append(chunk)

                remaining_text = current_chunk[split_at:].strip()
                overlap_text = self._get_overlap_text(
                    text=chunk,
                    chunk_overlap_chars=chunk_overlap_chars,
                )

                current_chunk = f"{overlap_text} {remaining_text}".strip()

        if current_chunk:
            chunks.extend(
                self._finalize_chunk(
                    text=current_chunk,
                    chunk_size_chars=chunk_size_chars,
                    chunk_overlap_chars=chunk_overlap_chars,
                )
            )

        return [chunk for chunk in chunks if chunk.strip()]

    def _finalize_chunk(
        self,
        text: str,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[str]:
        text = text.strip()

        if not text:
            return []

        if len(text) <= chunk_size_chars:
            return [text]

        chunks: list[str] = []
        current_text = text

        while len(current_text) > chunk_size_chars:
            split_at = self._find_split_position(
                text=current_text,
                max_chars=chunk_size_chars,
            )

            chunk = current_text[:split_at].strip()

            if chunk:
                chunks.append(chunk)

            remaining_text = current_text[split_at:].strip()
            overlap_text = self._get_overlap_text(
                text=chunk,
                chunk_overlap_chars=chunk_overlap_chars,
            )

            current_text = f"{overlap_text} {remaining_text}".strip()

        if current_text:
            chunks.append(current_text)

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split on sentence boundaries when possible.

        This is not perfect NLP sentence segmentation, but it is clean,
        dependency-free, and good enough for Phase 1.
        """

        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _find_split_position(self, text: str, max_chars: int) -> int:
        """
        Find a safe split point near max_chars.

        Prefer splitting on whitespace instead of cutting through words.
        """

        if len(text) <= max_chars:
            return len(text)

        split_at = text.rfind(" ", 0, max_chars)

        if split_at == -1 or split_at < max_chars // 2:
            return max_chars

        return split_at

    def _get_overlap_text(
        self,
        text: str,
        chunk_overlap_chars: int,
    ) -> str:
        if chunk_overlap_chars <= 0:
            return ""

        text = text.strip()

        if len(text) <= chunk_overlap_chars:
            return text

        overlap = text[-chunk_overlap_chars:].strip()

        first_space_index = overlap.find(" ")

        if first_space_index != -1:
            overlap = overlap[first_space_index + 1 :].strip()

        return overlap

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