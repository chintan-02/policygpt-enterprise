import re


class TextCleaningService:
    """
    Clean PDF-extracted text before chunking.

    Keep this simple for Phase 1:
    - remove noisy whitespace
    - repair common PDF spacing issues
    - infer simple section titles
    """

    ignored_title_prefixes = (
        "fictional demo hr policy",
        "public sample",
        "not legal advice",
        "page ",
        "field value",
        "table of contents",
        "suggested test questions",
    )

    common_spacing_repairs = {
        "fromanother": "from another",
        "inadvance": "in advance",
        "areemployees": "are employees",
        "effectivedate": "effective date",
        "localtime": "local time",
        "approvedfocused": "approved focused",
        "contractorsare": "contractors are",
        "employeesare": "employees are",
        "employeesmay": "employees may",
        "peopleoperations": "People Operations",
    }

    def clean_page_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\x00", " ")
        text = text.replace("\u00a0", " ")

        text = self._repair_common_spacing_issues(text)

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        text = re.sub(r"\n +", "\n", text)

        return text.strip()

    def infer_section_title(
        self,
        original_text: str,
        fallback: str | None = None,
    ) -> str | None:
        if not original_text:
            return fallback

        lines = [line.strip() for line in original_text.splitlines() if line.strip()]

        for line in lines[:12]:
            cleaned_line = self.clean_page_text(line)

            if not cleaned_line:
                continue

            if self._is_ignored_title(cleaned_line):
                continue

            if self._looks_like_numbered_section_title(cleaned_line):
                return cleaned_line

        for line in lines[:12]:
            cleaned_line = self.clean_page_text(line)

            if not cleaned_line:
                continue

            if self._is_ignored_title(cleaned_line):
                continue

            if self._looks_like_title(cleaned_line):
                return cleaned_line

        return fallback

    def _repair_common_spacing_issues(self, text: str) -> str:
        text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)
        text = re.sub(r"\bto(?=\d)", "to ", text, flags=re.IGNORECASE)

        for bad_text, fixed_text in self.common_spacing_repairs.items():
            text = re.sub(
                re.escape(bad_text),
                fixed_text,
                text,
                flags=re.IGNORECASE,
            )

        return text

    def _is_ignored_title(self, text: str) -> bool:
        normalized = text.lower().strip()

        return any(
            normalized.startswith(prefix)
            for prefix in self.ignored_title_prefixes
        )

    def _looks_like_numbered_section_title(self, text: str) -> bool:
        return bool(re.match(r"^\d+[\.\)]\s+[A-Z][A-Za-z0-9,/\- &]+", text))

    def _looks_like_title(self, text: str) -> bool:
        if len(text) > 90:
            return False

        if text.endswith("."):
            return False

        words = text.split()

        if len(words) > 12:
            return False

        alpha_chars = [char for char in text if char.isalpha()]

        if not alpha_chars:
            return False

        uppercase_or_title_words = 0

        for word in words:
            stripped = word.strip(":-–—,()[]{}")

            if not stripped:
                continue

            if stripped.isupper() or stripped[:1].isupper():
                uppercase_or_title_words += 1

        return uppercase_or_title_words >= max(1, len(words) // 2)