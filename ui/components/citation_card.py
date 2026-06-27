from __future__ import annotations

import re
from typing import Any

import streamlit as st


BOILERPLATE_PATTERNS = [
    r"Fictional demo HR policy for PolicyGPT Enterprise\s*-\s*public sample,\s*not legal advice\s*",
]


def _normalize_whitespace(text: str) -> str:
    """Collapse messy PDF spacing into readable text."""
    return re.sub(r"\s+", " ", text or "").strip()


def _remove_boilerplate(text: str) -> str:
    """Remove demo-document boilerplate that is not useful inside citation previews."""
    cleaned = text

    for pattern in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def _remove_repeated_source_prefix(
    text: str,
    page_number: str | int | None,
    section_title: str | None,
) -> str:
    """
    Remove repeated source labels from the beginning of excerpts.

    Example:
    "Page 7 5. Confidentiality, Data Privacy..." becomes cleaner because
    page and section are already shown in the citation metadata line.
    """
    cleaned = text.strip()

    page = str(page_number).strip() if page_number is not None else ""
    section = str(section_title or "").strip()

    prefix_patterns: list[str] = []

    if page and section:
        prefix_patterns.extend(
            [
                rf"^Page\s+{re.escape(page)}\s*{re.escape(section)}\s*",
                rf"^Page\s+{re.escape(page)}\s*[-–—:]*\s*{re.escape(section)}\s*",
            ]
        )

    if page:
        prefix_patterns.append(rf"^Page\s+{re.escape(page)}\s*[-–—:]*\s*")

    if section:
        prefix_patterns.append(rf"^{re.escape(section)}\s*[-–—:]*\s*")

    for pattern in prefix_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    return cleaned


def _remove_duplicate_leading_phrase(text: str) -> str:
    """
    Clean simple repeated phrase artifacts caused by PDF extraction.

    Example:
    "Confidential information Confidential information includes..."
    """
    words = text.split()

    if len(words) < 6:
        return text

    for phrase_len in range(2, 7):
        first_phrase = words[:phrase_len]
        second_phrase = words[phrase_len : phrase_len * 2]

        if first_phrase and first_phrase == second_phrase:
            return " ".join(words[phrase_len:]).strip()

    return text


def _truncate_text(text: str, max_chars: int = 520) -> str:
    """Keep citation previews readable in the UI."""
    cleaned = text.strip()

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def _clean_citation_preview(citation: dict[str, Any]) -> str:
    """Create a recruiter-friendly citation preview for the UI."""
    excerpt = str(citation.get("excerpt", "") or "")
    page_number = citation.get("page_number")
    section_title = citation.get("section_title")

    cleaned = _normalize_whitespace(excerpt)
    cleaned = _remove_boilerplate(cleaned)
    cleaned = _remove_repeated_source_prefix(cleaned, page_number, section_title)
    cleaned = _remove_duplicate_leading_phrase(cleaned)
    cleaned = _normalize_whitespace(cleaned)
    cleaned = _truncate_text(cleaned)

    return cleaned or "No citation preview text available."


def render_citation_card(
    citation: dict[str, Any],
    index: int,
    threshold: float | None = None,
) -> None:
    filename = citation.get("filename", "Unknown document")
    page_number = citation.get("page_number", "Unknown")
    section_title = citation.get("section_title") or "Unknown section"
    retrieval_score = float(citation.get("retrieval_score", 0.0))

    threshold_label = ""
    if threshold is not None:
        passed = retrieval_score >= threshold
        threshold_label = "Passed threshold" if passed else "Below threshold"

    source_line = (
        f"Page {page_number} · {section_title} · "
        f"Score {retrieval_score:.4f}"
    )

    if threshold_label:
        source_line += f" · {threshold_label}"

    preview_text = _clean_citation_preview(citation)

    with st.container(border=True):
        st.markdown(f"**Citation {index} — {filename}**")
        st.caption(source_line)

        st.markdown("**Source preview**")
        st.write(preview_text)

        st.progress(min(max(retrieval_score, 0.0), 1.0))