import re


class TextCleaningService:
    """
    Clean extracted PDF text before chunking.

    PDF extraction often creates broken lines, repeated spaces,
    odd unicode characters, and page-level formatting noise.
    """

    def clean_page_text(self, text: str) -> str:
        if not text:
            return ""

        text = self._normalize_unicode_spacing(text)
        text = self._join_broken_lines(text)
        text = self._normalize_punctuation_spacing(text)
        text = self._collapse_whitespace(text)

        return text.strip()

    def infer_section_title(
        self,
        original_text: str,
        fallback: str | None = None,
    ) -> str | None:
        """
        Basic section-title heuristic.

        Priority:
        1. Numbered policy section, for example: 5. Confidentiality...
        2. First meaningful non-header line
        3. Fallback
        """

        if not original_text:
            return fallback

        lines = [line.strip() for line in original_text.splitlines() if line.strip()]

        # Prefer numbered section titles.
        for line in lines:
            normalized_line = self._collapse_whitespace(line)

            if re.match(r"^\d+\.\s+.+", normalized_line):
                return normalized_line[:120]

        ignored_patterns = [
            r"^fictional demo hr policy",
            r"^public sample",
            r"^page\s+\d+$",
            r"^field\s+value$",
            r"^table of contents$",
        ]

        for line in lines:
            normalized_line = self._collapse_whitespace(line)
            lowered = normalized_line.lower()

            should_ignore = any(
                re.match(pattern, lowered) for pattern in ignored_patterns
            )

            if should_ignore:
                continue

            if 3 <= len(normalized_line) <= 100:
                return normalized_line

        return fallback

    def _normalize_unicode_spacing(self, text: str) -> str:
        replacements = {
            "\u00a0": " ",
            "\u200b": "",
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _join_broken_lines(self, text: str) -> str:
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