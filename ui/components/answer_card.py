from typing import Any

import streamlit as st

from ui.components.badges import (
    confidence_variant,
    evidence_variant,
    provider_variant,
    render_badge_row,
)


def render_answer_card(answer_data: dict[str, Any], latency_ms: float | None = None) -> None:
    answer = answer_data.get("answer", "")
    evidence_status = answer_data.get("evidence_status", "unknown")
    confidence_score = float(answer_data.get("confidence_score", 0.0))
    citation_count = int(answer_data.get("citation_count", 0))
    llm_provider = answer_data.get("llm_provider", "unknown")
    model_name = answer_data.get("model_name") or "None"
    fallback_used = bool(answer_data.get("fallback_used", False))
    answer_ready = bool(answer_data.get("answer_ready", False))

    if fallback_used or not answer_ready:
        st.markdown(
            f"""
            <div class="pgpt-fallback">
                <div class="pgpt-card-title">No reliable generated answer</div>
                <div class="pgpt-muted">{answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="pgpt-card">
                <div class="pgpt-small-label">Answer</div>
                <div class="pgpt-answer">{answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    badges = [
        ("Evidence", evidence_status.title(), evidence_variant(evidence_status)),
        ("Confidence", f"{confidence_score:.4f}", confidence_variant(confidence_score)),
        ("Citations", str(citation_count), "neutral"),
        ("Provider", llm_provider, provider_variant(llm_provider)),
        ("Model", model_name, "neutral"),
        ("Fallback", str(fallback_used), "warning" if fallback_used else "success"),
    ]

    if latency_ms is not None:
        badges.append(("Latency", f"{latency_ms:.0f} ms", "neutral"))

    render_badge_row(badges)

    st.caption(
        "PolicyGPT answers only from uploaded document evidence. "
        "If evidence is insufficient, generation is skipped."
    )