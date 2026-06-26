import streamlit as st

from ui.components.cards import render_metric_card, render_page_header
from ui.styles import load_global_styles


load_global_styles()

render_page_header(
    title="Architecture",
    subtitle=(
        "PolicyGPT Enterprise is a production-shaped RAG assistant for HR, SOP, "
        "policy, and compliance document intelligence."
    ),
)

col1, col2, col3 = st.columns(3)

with col1:
    render_metric_card(
        label="Phase",
        value="Phase 1",
        caption="Core RAG MVP",
    )

with col2:
    render_metric_card(
        label="Backend",
        value="FastAPI",
        caption="Upload, retrieval, answers",
    )

with col3:
    render_metric_card(
        label="Vector DB",
        value="ChromaDB",
        caption="Local persistent store",
    )

st.subheader("System flow")

st.markdown(
    """
    <div class="pgpt-flow">
        <div class="pgpt-flow-step">1. User uploads policy PDF</div>
        <div class="pgpt-flow-step">2. PyMuPDF extracts page-level text</div>
        <div class="pgpt-flow-step">3. Text cleaning repairs noisy PDF extraction</div>
        <div class="pgpt-flow-step">4. Chunking preserves document, page, section, and chunk metadata</div>
        <div class="pgpt-flow-step">5. SentenceTransformer creates local embeddings</div>
        <div class="pgpt-flow-step">6. ChromaDB stores vectors and metadata</div>
        <div class="pgpt-flow-step">7. Retrieval finds relevant policy chunks</div>
        <div class="pgpt-flow-step">8. Evidence threshold decides if generation is allowed</div>
        <div class="pgpt-flow-step">9. Groq/OpenAI/no-LLM provider layer generates or safely falls back</div>
        <div class="pgpt-flow-step">10. UI returns answer, confidence, provider, and citation cards</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Trust and safety behavior")

st.markdown(
    """
    <div class="pgpt-card">
        <div class="pgpt-card-title">Evidence-gated generation</div>
        <div class="pgpt-muted">
            PolicyGPT does not blindly call an LLM. The backend first retrieves evidence,
            scores it, filters it by threshold, and only then allows generation.
            If no evidence passes the threshold, the system returns a fallback message.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="pgpt-card">
        <div class="pgpt-card-title">Citation card design</div>
        <div class="pgpt-muted">
            Citation cards expose document name, page number, section title,
            retrieval score, and a short excerpt. The LLM receives longer hidden
            evidence text for grounding, while the UI stays clean and readable.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Current build scope")

st.code(
    """
Phase 1 — Core RAG MVP
✅ FastAPI backend
✅ PDF upload
✅ PDF text extraction
✅ Text cleaning
✅ Chunking with metadata
✅ Local embeddings
✅ ChromaDB vector store
✅ Retrieval pipeline
✅ Citation cards
✅ Confidence scoring
✅ Unsupported-answer fallback
✅ Provider-agnostic LLM layer
✅ Streamlit Compliance Intelligence Console

Phase 2 — Later
- Evaluation dashboard
- PostgreSQL metadata
- Docker Compose
- Logging dashboard
- RAG evaluation
    """,
    language="text",
)