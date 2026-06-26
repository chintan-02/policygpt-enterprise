from typing import Any

import streamlit as st

from ui.components.badges import (
    confidence_variant,
    evidence_variant,
    render_badge_row,
)


def render_evidence_summary(
    evidence_data: dict[str, Any],
    latency_ms: float | None = None,
) -> None:
    evidence_status = evidence_data.get("evidence_status", "unknown")
    confidence_score = float(evidence_data.get("confidence_score", 0.0))
    citation_count = int(evidence_data.get("citation_count", 0))
    min_score = float(evidence_data.get("min_retrieval_score", 0.0))
    answer_ready = bool(evidence_data.get("answer_ready", False))

    badges = [
        ("Evidence", evidence_status.title(), evidence_variant(evidence_status)),
        ("Confidence", f"{confidence_score:.4f}", confidence_variant(confidence_score)),
        ("Citations", str(citation_count), "neutral"),
        ("Threshold", f"{min_score:.2f}", "neutral"),
        ("Generation allowed", str(answer_ready), "success" if answer_ready else "danger"),
    ]

    if latency_ms is not None:
        badges.append(("Latency", f"{latency_ms:.0f} ms", "neutral"))

    render_badge_row(badges)


def render_retrieval_trace(data: dict[str, Any]) -> None:
    citation_count = int(data.get("citation_count", 0))
    answer_ready = bool(data.get("answer_ready", False))
    evidence_status = data.get("evidence_status", "unknown")

    if citation_count == 0:
        retrieval_step = "No chunks passed the relevance threshold."
    else:
        retrieval_step = f"{citation_count} citation card(s) passed the relevance threshold."

    if answer_ready:
        generation_step = "LLM generation is allowed because evidence is available."
    else:
        generation_step = "LLM generation is skipped because evidence is insufficient."

    st.markdown(
        """
        <div class="pgpt-flow">
            <div class="pgpt-card-title">Retrieval trace</div>
            <div class="pgpt-flow-step">1. Question embedded into semantic vector</div>
            <div class="pgpt-flow-step">2. ChromaDB retrieved candidate chunks</div>
            <div class="pgpt-flow-step">3. Evidence score threshold applied</div>
            <div class="pgpt-flow-step">4. Citation cards prepared</div>
            <div class="pgpt-flow-step">5. Generation allowed only if evidence passes</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(f"Evidence status: {evidence_status}. {retrieval_step} {generation_step}")