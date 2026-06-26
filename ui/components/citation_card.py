from typing import Any

import streamlit as st


def render_citation_card(
    citation: dict[str, Any],
    index: int,
    threshold: float | None = None,
) -> None:
    filename = citation.get("filename", "Unknown document")
    page_number = citation.get("page_number", "Unknown")
    section_title = citation.get("section_title") or "Unknown section"
    excerpt = citation.get("excerpt", "")
    retrieval_score = float(citation.get("retrieval_score", 0.0))

    threshold_label = ""

    if threshold is not None:
        passed = retrieval_score >= threshold
        threshold_label = "Passed threshold" if passed else "Below threshold"

    with st.container(border=True):
        st.markdown(f"**Citation {index} — {filename}**")

        meta_text = (
            f"Page {page_number} · {section_title} · "
            f"Score {retrieval_score:.4f}"
        )

        if threshold_label:
            meta_text += f" · {threshold_label}"

        st.caption(meta_text)

        st.write(excerpt)

        st.progress(min(max(retrieval_score, 0.0), 1.0))