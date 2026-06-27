from ui.components.feedback import (
    render_error_state,
    render_no_answer_state,
    render_no_citations_state,
    render_no_document_state,
    render_success_state,
)

import streamlit as st

from ui.api_client import PolicyGPTAPIError, ask_question, get_backend_health, upload_document
from ui.components.answer_card import render_answer_card
from ui.components.cards import (
    render_backend_status_card,
    render_page_header,
    render_upload_summary,
)
from ui.components.citation_card import render_citation_card
from ui.components.evidence_panel import render_retrieval_trace
from ui.state import DEMO_QUESTIONS, initialize_session_state
from ui.styles import load_global_styles


initialize_session_state()
load_global_styles()

render_page_header(
    title="Ask PolicyGPT",
    subtitle=(
        "Ask HR, policy, SOP, or compliance questions. "
        "Answers are generated only when retrieved document evidence passes the threshold."
    ),
)

with st.sidebar:
    st.subheader("System status")
    backend_status = get_backend_health()
    render_backend_status_card(backend_status)

    st.divider()

    st.subheader("Demo questions")
    for index, question in enumerate(DEMO_QUESTIONS, start=1):
        if st.button(question, key=f"ask_demo_question_{index}", use_container_width=True):
            st.session_state.question_text = question

    st.divider()

    st.caption(
        "Run FastAPI first: "
        "`uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000`"
    )


upload_col, ask_col = st.columns([0.9, 1.35], gap="large")

with upload_col:
    st.markdown(
        """
        <div class="pgpt-card">
            <div class="pgpt-card-title">Document ingestion</div>
            <div class="pgpt-muted">
                Upload a policy PDF and index it into ChromaDB before asking questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        label="Upload policy PDF",
        type=["pdf"],
        help="Upload a selectable-text PDF. Scanned PDFs may not extract text.",
    )

    if st.button(
        "Index document",
        type="primary",
        disabled=uploaded_file is None,
        use_container_width=True,
    ):
        if uploaded_file is not None:
            try:
                with st.spinner(
                    "Indexing policy PDF: extracting text, chunking, embedding, and storing in ChromaDB..."
                ):
                    upload_data, latency_ms = upload_document(
                        filename=uploaded_file.name,
                        file_bytes=uploaded_file.getvalue(),
                    )

                st.session_state.last_upload = upload_data
                st.session_state.last_upload_latency_ms = latency_ms

                # Clear old answer when a new document is indexed.
                st.session_state.last_answer = None
                st.session_state.last_answer_latency_ms = None

                render_success_state(
                    title="Document indexed successfully.",
                    message="PDF uploaded, text extracted, chunks embedded, and stored in ChromaDB.",
                )

            except PolicyGPTAPIError as exc:
                render_error_state(
                    title="Document indexing failed",
                    message=str(exc),
                    fix_hint="Check that the backend is running and the file is a readable PDF.",
                )

            except Exception:
                render_error_state(
                    title="Document indexing failed",
                    message=(
                        "PolicyGPT could not index this PDF. The file may be invalid, too large, "
                        "or the backend may not be running."
                    ),
                    fix_hint="Check backend logs and confirm the file is a readable PDF.",
                )

    if st.session_state.last_upload:
        render_upload_summary(
            st.session_state.last_upload,
            st.session_state.last_upload_latency_ms,
        )

with ask_col:
    st.markdown(
        """
        <div class="pgpt-card">
            <div class="pgpt-card-title">Question</div>
            <div class="pgpt-muted">
                PolicyGPT will retrieve evidence first, then generate only if evidence is sufficient.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("ask_policygpt_form"):
        question = st.text_area(
            "Ask a policy question",
            key="question_text",
            height=115,
        )

        top_k = st.slider(
            "Candidate chunks to retrieve",
            min_value=1,
            max_value=10,
            value=5,
            help="The backend will still filter results using the evidence threshold.",
        )

        submitted = st.form_submit_button(
            "Generate citation-backed answer",
            type="primary",
            use_container_width=True,
        )

feedback_rendered = False

if submitted:
    if not st.session_state.last_upload:
        render_no_document_state()
        feedback_rendered = True

    elif not question.strip():
        render_error_state(
            title="Question is empty",
            message="Enter a policy question before generating an answer.",
            fix_hint="Example: What is the remote work equipment allowance?",
        )
        feedback_rendered = True

    else:
        try:
            with st.spinner("Retrieving evidence and generating answer..."):
                answer_data, latency_ms = ask_question(
                    question=question.strip(),
                    top_k=top_k,
                )

            st.session_state.last_answer = answer_data
            st.session_state.last_answer_latency_ms = latency_ms

        except PolicyGPTAPIError as exc:
            render_error_state(
                title="Request failed",
                message=str(exc),
                fix_hint="Check that the FastAPI backend is running and the document has been indexed.",
            )
            feedback_rendered = True


if st.session_state.last_answer and st.session_state.last_upload:
    st.divider()

    answer_data = st.session_state.last_answer

    render_answer_card(
        answer_data=answer_data,
        latency_ms=st.session_state.last_answer_latency_ms,
    )

    with st.expander("Retrieval trace", expanded=False):
        render_retrieval_trace(answer_data)

    st.subheader("Citation cards")

    citations = answer_data.get("citations", [])

    if citations:
        for index, citation in enumerate(citations, start=1):
            render_citation_card(
                citation=citation,
                index=index,
            )
    else:
        render_no_citations_state()

elif st.session_state.last_upload and not feedback_rendered:
    render_no_answer_state()

elif not feedback_rendered:
    render_no_document_state()