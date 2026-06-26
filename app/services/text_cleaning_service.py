import re


class TextCleaningService:
    """
    Clean extracted PDF text before chunking.

    PDF extraction often creates broken lines, repeated spaces,
    odd unicode characters, and page-level formatting noise.

    Keep this service focused only on cleaning.
    Do not put chunking, embeddings, or retrieval logic here.
    """

    def clean_page_text(self, text: str) -> str:
        if not text:
            return ""

        text = self._normalize_unicode_spacing(text)
        text = self._join_broken_lines(text)
        text = self._normalize_punctuation_spacing(text)
        text = self._collapse_whitespace(text)

        return text.strip()

    def infer_section_title(self, original_text: str, fallback: str | None = None) -> str | None:
        """
        Basic section-title heuristic.

        Later we can improve this using PDF font sizes or layout metadata.
        For now, we use the first meaningful short line.
        """

        if not original_text:
            return fallback

        lines = [line.strip() for line in original_text.splitlines() if line.strip()]

        for line in lines:
            normalized_line = self._collapse_whitespace(line)

            if 3 <= len(normalized_line) <= 80:
                return normalized_line

        return fallback

    def _normalize_unicode_spacing(self, text: str) -> str:
        replacements = {
            "\u00a0": " ",  # non-breaking space
            "\u200b": "",   # zero-width space
            "\u2013": "-",  # en dash
            "\u2014": "-",  # em dash
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _join_broken_lines(self, text: str) -> str:
        """
        Convert PDF line breaks into readable text.

        Example:
        ChemiCutes
        turns
        real
        science

        becomes:
        ChemiCutes turns real science
        """

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        if not lines:
            return ""

        return " ".join(lines)

    def _normalize_punctuation_spacing(self, text: str) -> str:
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"([({\[])\s+", r"\1", text)
        text = re.sub(r"\s+([)}\]])", r"\1", text)
        return text

    def _collapse_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()