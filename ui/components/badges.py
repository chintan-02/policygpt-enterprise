import streamlit as st


def _badge_html(label: str, value: str, variant: str = "neutral") -> str:
    return (
        f'<span class="pgpt-badge pgpt-badge-{variant}">'
        f"{label}: {value}"
        f"</span>"
    )


def render_badge(label: str, value: str, variant: str = "neutral") -> None:
    st.markdown(_badge_html(label, value, variant), unsafe_allow_html=True)


def render_badge_row(badges: list[tuple[str, str, str]]) -> None:
    html = '<div class="pgpt-badge-row">'

    for label, value, variant in badges:
        html += _badge_html(label, value, variant)

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def evidence_variant(evidence_status: str) -> str:
    normalized = evidence_status.lower()

    if normalized == "strong":
        return "success"

    if normalized == "moderate":
        return "info"

    if normalized == "weak":
        return "warning"

    return "danger"


def confidence_variant(score: float) -> str:
    if score >= 0.75:
        return "success"

    if score >= 0.5:
        return "info"

    if score > 0:
        return "warning"

    return "danger"


def provider_variant(provider: str) -> str:
    normalized = provider.lower()

    if normalized in {"groq", "openai"}:
        return "success"

    if normalized == "none":
        return "warning"

    return "neutral"