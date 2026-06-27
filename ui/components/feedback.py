from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str,
    message: str,
    action_hint: str | None = None,
) -> None:
    """Render a clean empty state for first-load or missing-result UI."""
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(message)

        if action_hint:
            st.caption(action_hint)


def render_error_state(
    title: str,
    message: str,
    fix_hint: str | None = None,
) -> None:
    """Render a clear error state without exposing raw internal details."""
    st.error(f"**{title}**")

    with st.container(border=True):
        st.write(message)

        if fix_hint:
            st.caption(f"Suggested fix: {fix_hint}")


def render_success_state(
    title: str,
    message: str,
) -> None:
    """Render a lightweight success state."""
    st.success(f"**{title}**")
    st.caption(message)


def render_warning_state(
    title: str,
    message: str,
) -> None:
    """Render a clean warning state."""
    st.warning(f"**{title}**")
    st.caption(message)


def render_backend_disconnected_state() -> None:
    """Render a friendly backend unavailable message."""
    render_error_state(
        title="Backend is not connected",
        message=(
            "PolicyGPT cannot reach the FastAPI backend right now. "
            "Start the backend before uploading documents or asking questions."
        ),
        fix_hint="Run: uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000",
    )


def render_no_document_state() -> None:
    """Render empty state when no PDF has been indexed yet."""
    render_empty_state(
        title="No policy document indexed yet",
        message=(
            "Upload a policy PDF and click **Index document** before asking questions. "
            "PolicyGPT needs indexed document evidence before it can generate citation-backed answers."
        ),
        action_hint="Demo file: examples/sample_hr_policy.pdf",
    )


def render_no_answer_state() -> None:
    """Render empty state before the first question is answered."""
    render_empty_state(
        title="Ask a policy question to begin",
        message=(
            "After a document is indexed, ask a policy, HR, SOP, or compliance question. "
            "PolicyGPT will retrieve evidence first and generate only if the evidence passes the threshold."
        ),
        action_hint="Example: Can employees paste confidential data into public AI tools?",
    )


def render_no_citations_state() -> None:
    """Render empty state when no citations are returned."""
    render_empty_state(
        title="No citation cards returned",
        message=(
            "No retrieved document chunks passed the evidence threshold for this question. "
            "The system skipped generation to avoid unsupported answers."
        ),
        action_hint="Try rephrasing the question or upload a document that contains the relevant policy.",
    )