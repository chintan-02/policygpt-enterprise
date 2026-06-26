import streamlit as st

from ui.api_client import PolicyGPTAPIError, get_backend_health, retrieve_evidence
from ui.components.cards import render_backend_status_card, render_page_header
from ui.components.citation_card import render_citation_card
from ui.components.evidence_panel import render_evidence_summary, render_retrieval_trace
from ui.state import DEMO_QUESTIONS, initialize_session_state
from ui.styles import load_global_styles


initialize_session_state()
load_global_styles()

render_page_header(
    title="Evidence Explorer",
    subtitle=(
        "Inspect retrieved chunks, page citations, section metadata, retrieval scores, "
        "and evidence threshold behavior before generation."
    ),
)

with st.sidebar:
    st.subheader("System status")
    render_backend_status_card(get_backend_health())

    st.divider()

    st.subheader("Evidence test questions")
    for index, question in enumerate(DEMO_QUESTIONS, start=1):
        if st.button(question, key=f"evidence_demo_question_{index}", use_container_width=True):
            st.session_state.evidence_query = question


with st.form("evidence_explorer_form"):
    query = st.text_area(
        "Evidence query",
        key="evidence_query",
        height=105,
    )

    top_k = st.slider(
        "Candidate chunks to retrieve",
        min_value=1,
        max_value=10,
        value=5,
    )

    submitted = st.form_submit_button(
        "Retrieve evidence",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not query.strip():
        st.warning("Enter a query first.")
    else:
        try:
            with st.spinner("Retrieving citation evidence..."):
                evidence_data, latency_ms = retrieve_evidence(
                    query=query.strip(),
                    top_k=top_k,
                )

            st.session_state.last_evidence = evidence_data
            st.session_state.last_evidence_latency_ms = latency_ms
        except PolicyGPTAPIError as exc:
            st.error(str(exc))


if st.session_state.last_evidence:
    st.divider()

    evidence_data = st.session_state.last_evidence

    render_evidence_summary(
        evidence_data=evidence_data,
        latency_ms=st.session_state.last_evidence_latency_ms,
    )

    with st.expander("Retrieval trace", expanded=True):
        render_retrieval_trace(evidence_data)

    st.subheader("Retrieved citation cards")

    citations = evidence_data.get("citations", [])
    threshold = float(evidence_data.get("min_retrieval_score", 0.0))

    if not citations:
        st.info(
            "No citation cards passed the retrieval threshold. "
            "Try rephrasing the query or uploading a more relevant policy document."
        )
    else:
        for index, citation in enumerate(citations, start=1):
            render_citation_card(
                citation=citation,
                index=index,
                threshold=threshold,
            )