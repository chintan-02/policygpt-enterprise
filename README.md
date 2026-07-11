# PolicyGPT Enterprise — Evidence-First RAG for Policy & Compliance Documents

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-FF6446?style=flat-square)
![SentenceTransformers](https://img.shields.io/badge/Embeddings-SentenceTransformers-FFB000?style=flat-square)
![Status](https://img.shields.io/badge/Status-Phase_1_MVP-F59E0B?style=flat-square)

**A production-shaped Retrieval-Augmented Generation platform that retrieves and scores document evidence before answer generation.**

[Portfolio Case Study](https://chintan-patel-ai.netlify.app/case-studies/policygpt)

</div>

---

> [!IMPORTANT]
> PolicyGPT Enterprise is a portfolio and educational document-intelligence project. It is not legal advice, an official compliance decision engine, or a production governance system. Real organizational use would require security review, access control, privacy assessment, evaluation, monitoring, policy-owner approval, and controlled deployment.

---

## Product Overview

PolicyGPT Enterprise helps users explore HR policies, SOPs, internal guidance, and compliance documents through an evidence-first RAG workflow.

Users upload a PDF and ask a natural-language question. Before generating an answer, the system:

1. retrieves relevant document chunks
2. scores the retrieved evidence
3. applies a configurable threshold
4. builds page-level citation cards
5. generates only when supporting evidence is available
6. returns a safe fallback when evidence is weak or unsupported

```text
Question
   ↓
Semantic Retrieval
   ↓
Evidence Scoring
   ↓
Threshold Decision
   ├── Supported → Generate Answer + Citations
   └── Unsupported → Safe Fallback
```

This is intentionally different from a generic PDF chatbot. The interface exposes evidence status, confidence, sources, provider information, and fallback behavior so users can inspect how the answer was produced.

---

## Project Status

**Current phase:** Phase 1 — Core RAG MVP

### Implemented

- FastAPI backend with documented REST endpoints
- PDF validation and upload workflow
- page-level text extraction with PyMuPDF
- extracted-text cleaning and common spacing repair
- page-aware chunking with document metadata
- local SentenceTransformer embeddings
- persistent local ChromaDB vector storage
- semantic search and evidence retrieval
- configurable retrieval-score threshold
- evidence-status and confidence calculation
- duplicate-citation filtering
- page-level citation cards
- evidence-gated answer generation
- Groq answer-generation mode
- OpenAI answer-generation mode
- no-LLM evidence-only fallback mode
- unsupported-question fallback
- Streamlit Compliance Intelligence Console
- Evidence Explorer page
- Architecture page
- loading, empty, disconnected, and error states
- safe health response that does not expose API keys
- fictional sample HR policy for demonstration
- Dockerfile for container packaging

### Planned

- formal RAG evaluation and test datasets
- retrieval and faithfulness metrics
- confidence analytics dashboard
- PostgreSQL document metadata storage
- Docker Compose
- authentication and role-based access control
- document deletion and lifecycle management
- multi-document comparison
- compliance-summary and report generation
- latency, retrieval-score, token, and cost analytics
- production monitoring and observability
- CI/CD pipeline
- cloud deployment

> Planned capabilities are roadmap targets and are not presented as completed project experience.

---

## Why This Project Matters

Many introductory RAG applications follow this pattern:

```text
Upload PDF
   ↓
Retrieve chunks
   ↓
Always ask an LLM to answer
```

That workflow can produce confident responses even when the retrieved evidence is weak.

PolicyGPT follows a safer pattern:

```text
Retrieve
   ↓
Score
   ↓
Verify threshold
   ↓
Generate only when supported
   ↓
Return answer + confidence + citations
```

When the system cannot find enough supporting evidence, it does not invent policy details. It returns a fallback response and exposes that the evidence was insufficient.

This design is more appropriate for document-intelligence scenarios where answers need to be:

- grounded
- reviewable
- source-linked
- explainable
- failure-aware

---

## Core Capabilities

### Evidence-Gated Generation

The backend does not call the selected LLM blindly.

Before generation, PolicyGPT:

1. embeds the user question
2. searches ChromaDB for candidate chunks
3. evaluates retrieval scores
4. filters evidence below the configured threshold
5. removes duplicate citations
6. creates citation cards
7. calculates evidence status and confidence
8. allows generation only when evidence is sufficient

If evidence is insufficient, the system skips normal generation and returns a safe fallback.

---

### Citation-Backed Answers

Supported answers include citation cards containing:

- document name
- page number
- inferred section title
- readable excerpt
- retrieval score

This makes the result auditable rather than purely conversational.

---

### Evidence Explorer

The Evidence Explorer allows users to inspect retrieval before answer generation.

It displays:

- evidence status
- confidence score
- configured threshold
- retrieval trace
- candidate citations
- page and section metadata
- individual retrieval scores

This helps users understand why the system did or did not allow generation.

---

### Provider-Agnostic Answer Layer

PolicyGPT supports three answer modes:

| Mode | Behavior |
|---|---|
| Groq | Generates an answer through the configured Groq model |
| OpenAI | Generates an answer through the configured OpenAI model |
| No-LLM fallback | Returns available evidence without requiring generation |

The retrieval pipeline is separated from the answer provider. This allows the system to preserve evidence and citations even when generation is disabled or unavailable.

---

### Failure-Aware Behavior

The application handles several important states:

- backend unavailable
- no document uploaded
- PDF selected but not indexed
- upload or parsing failure
- insufficient retrieval evidence
- provider disabled or misconfigured
- answer-generation failure
- no citations returned

The interface communicates these states rather than silently failing or presenting unsupported output.

---

### Clean Evidence Presentation

The backend separates longer grounding text from shorter UI excerpts:

```text
evidence_text → longer context used for answer grounding
excerpt       → shorter text shown in citation cards
```

This provides sufficient context to the answer-generation layer while keeping the interface readable.

---

## Application Screenshots

### Document Ingestion Console

The dashboard shows backend connectivity, PDF upload, indexing status, page count, chunk count, stored vector count, and collection information.

<img src="screenshots/01-dashboard-upload.png" alt="PolicyGPT document ingestion dashboard" width="900"/>

---

### Citation-Backed Answer

The system retrieves evidence, verifies the threshold, generates a grounded answer, and returns page-level citation cards.

<img src="screenshots/02-citation-backed-answer.png" alt="PolicyGPT citation-backed answer with evidence score and citation card" width="900"/>

---

### AI Policy and Data Privacy Question

A compliance-style question is answered using evidence from the uploaded policy document.

<img src="screenshots/03-ai-policy-answer.png" alt="PolicyGPT AI policy answer with strong evidence and citations" width="900"/>

---

### Unsupported Question Fallback

When the uploaded document does not support the question, generation is skipped and a safe fallback is returned.

<img src="screenshots/04-unsupported-fallback.png" alt="PolicyGPT unsupported question fallback with no citations" width="900"/>

---

### Evidence Explorer

The Evidence Explorer exposes retrieval status, confidence, threshold, trace information, and citation cards before generation.

<img src="screenshots/05-evidence-explorer.png" alt="PolicyGPT evidence explorer with retrieval trace and citation cards" width="900"/>

---

### Architecture Page

The application includes a visual explanation of the complete RAG workflow.

<img src="screenshots/06-architecture-page.png" alt="PolicyGPT architecture page showing RAG system flow" width="900"/>

---

### FastAPI Documentation

The backend exposes documented endpoints for health, ingestion, search, evidence retrieval, and question answering.

<img src="screenshots/07-fastapi-docs.png" alt="PolicyGPT FastAPI Swagger documentation" width="900"/>

---

## High-Level Architecture

```text
User
  │
  ▼
Streamlit Compliance Intelligence Console
  │
  ▼
FastAPI Backend
  │
  ├── PDF Validation
  ├── PyMuPDF Text Extraction
  ├── Text Cleaning
  ├── Page-Aware Chunking
  ├── SentenceTransformer Embeddings
  ├── ChromaDB Vector Storage
  ├── Semantic Retrieval
  ├── Evidence Scoring
  ├── Threshold Filtering
  ├── Citation Construction
  └── Answer Generation
         ├── Groq
         ├── OpenAI
         └── No-LLM Fallback
```

---

## Request Flows

### Document Upload

```text
POST /api/v1/documents/upload
   ↓
Validate file type and size
   ↓
Read PDF bytes
   ↓
Extract page-level text
   ↓
Clean text and repair spacing
   ↓
Infer section titles
   ↓
Create overlapping chunks
   ↓
Generate embeddings
   ↓
Store chunks in ChromaDB
   ↓
Return ingestion summary
```

### Evidence Retrieval

```text
POST /api/v1/documents/evidence
   ↓
Embed user question
   ↓
Search ChromaDB
   ↓
Apply retrieval threshold
   ↓
Remove duplicate citations
   ↓
Build citation cards
   ↓
Calculate confidence
   ↓
Return evidence response
```

### Question Answering

```text
POST /api/v1/documents/ask
   ↓
Retrieve and score evidence
   ↓
Check evidence status
   ├── Insufficient → Return fallback
   └── Supported
          ↓
       Build grounding context
          ↓
       Call configured provider
          ↓
       Return answer + confidence + citations
```

---

## Backend Service Design

FastAPI route handlers remain thin and delegate business logic to service classes.

| Service | Responsibility |
|---|---|
| `PDFExtractionService` | Extract page-level text from uploaded PDF files |
| `TextCleaningService` | Clean extracted text and repair common PDF spacing issues |
| `ChunkingService` | Create chunks while preserving document, page, section, and chunk metadata |
| `EmbeddingService` | Generate local SentenceTransformer embeddings |
| `VectorStoreService` | Store and search embeddings in ChromaDB |
| `RetrievalService` | Retrieve evidence, apply score thresholds, remove duplicates, and create citations |
| `AnswerGenerationService` | Generate evidence-grounded answers through Groq, OpenAI, or fallback |
| `DocumentService` | Coordinate ingestion, retrieval, and answer workflows |

---

## Frontend Design

The Streamlit frontend is organized into product pages and reusable components.

### Pages

| Page | Purpose |
|---|---|
| Ask PolicyGPT | Upload a document, ask questions, and inspect answers and citations |
| Evidence Explorer | Inspect retrieval results before answer generation |
| Architecture | Review the end-to-end system design |

### Reusable UI Components

| Component | Purpose |
|---|---|
| `answer_card.py` | Display a generated answer or fallback response |
| `citation_card.py` | Display source document, page, section, excerpt, and score |
| `badges.py` | Display evidence, confidence, provider, model, and fallback status |
| `cards.py` | Provide reusable layout and summary cards |
| `evidence_panel.py` | Display retrieval trace and evidence summary |
| `styles.py` | Apply the application’s custom product styling |

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Check backend health and safe configuration status |
| `POST` | `/api/v1/documents/upload` | Upload, process, and index a PDF |
| `POST` | `/api/v1/documents/search` | Run raw semantic search |
| `POST` | `/api/v1/documents/evidence` | Retrieve scored citation evidence |
| `POST` | `/api/v1/documents/ask` | Generate an evidence-gated answer |

Interactive API documentation is available locally at:

```text
http://localhost:8000/docs
```

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Language | Python |
| Backend | FastAPI, Pydantic v2 |
| PDF processing | PyMuPDF |
| Embeddings | SentenceTransformers |
| Vector storage | ChromaDB |
| Generation | Groq API, OpenAI SDK, no-LLM fallback |
| Frontend | Streamlit, custom CSS, reusable components |
| Configuration | Pydantic Settings, `.env` |
| Logging | structlog and Python logging |
| Packaging | Dockerfile |
| Local storage | ChromaDB persistent directory |

---

## Project Structure

```text
policygpt-enterprise/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── health.py
│   │       └── documents.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   └── prompts.py
│   │
│   ├── schemas/
│   │   └── document.py
│   │
│   └── services/
│       ├── answer_generation_service.py
│       ├── chunking_service.py
│       ├── document_service.py
│       ├── embedding_service.py
│       ├── pdf_extraction_service.py
│       ├── retrieval_service.py
│       ├── text_cleaning_service.py
│       └── vector_store_service.py
│
├── ui/
│   ├── app.py
│   ├── api_client.py
│   ├── config.py
│   ├── state.py
│   ├── styles.py
│   │
│   ├── components/
│   │   ├── answer_card.py
│   │   ├── badges.py
│   │   ├── cards.py
│   │   ├── citation_card.py
│   │   └── evidence_panel.py
│   │
│   └── pages/
│       ├── ask.py
│       ├── evidence.py
│       └── architecture.py
│
├── docs/
│   ├── api_examples.md
│   ├── demo_script.md
│   └── smoke_test_checklist.md
│
├── examples/
│   └── sample_hr_policy.pdf
│
├── screenshots/
│   ├── 01-dashboard-upload.png
│   ├── 02-citation-backed-answer.png
│   ├── 03-ai-policy-answer.png
│   ├── 04-unsupported-fallback.png
│   ├── 05-evidence-explorer.png
│   ├── 06-architecture-page.png
│   └── 07-fastapi-docs.png
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   └── chroma/
│
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/chintan-02/policygpt-enterprise.git
cd policygpt-enterprise
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the environment file

```bash
cp .env.example .env
```

Add the required configuration and provider key to `.env`.

> Never commit a real `.env` file or API key.

---

## Environment Configuration

A typical local configuration is:

```env
APP_NAME=PolicyGPT Enterprise
APP_ENV=development
APP_VERSION=0.1.0
DEBUG=true

API_PREFIX=/api/v1
LOG_LEVEL=INFO

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

CORS_ALLOWED_ORIGINS=http://localhost:8501,http://localhost:3000,http://localhost:5173
MAX_PDF_UPLOAD_SIZE_MB=10

TEXT_CHUNK_SIZE_CHARS=1200
TEXT_CHUNK_OVERLAP_CHARS=200

EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32

CHROMA_PERSIST_DIRECTORY=data/chroma
CHROMA_COLLECTION_NAME=policygpt_documents

SEARCH_TOP_K_DEFAULT=5
MIN_RETRIEVAL_SCORE=0.45
CITATION_EXCERPT_MAX_CHARS=450
LLM_EVIDENCE_MAX_CHARS=1200
MAX_CITATION_CARDS=5

ENABLE_LLM_ANSWER=true
LLM_PROVIDER=groq
LLM_MAX_OUTPUT_TOKENS=700
LLM_TEMPERATURE=0.1

GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL_NAME=llama-3.3-70b-versatile

OPENAI_API_KEY=
OPENAI_MODEL_NAME=gpt-4o-mini
```

Configuration values can be adjusted for local experiments. Production environments would require secure secret storage rather than a local `.env` file.

---

## Run the Backend

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## Run the Streamlit Interface

Open a second terminal and activate the same environment:

```bash
source .venv/bin/activate
streamlit run ui/app.py
```

Open:

```text
http://localhost:8501
```

---

## Demo Document

The repository includes a fictional sample HR policy:

```text
examples/sample_hr_policy.pdf
```

The file is intended for public demonstration and does not contain real employee data, confidential company information, or legal advice.

---

## Demo Questions

After uploading the sample document, try:

```text
What is the remote work equipment allowance?
Can employees paste confidential data into public AI tools?
How many days in advance should employees request planned vacation?
What should employees do if they see harassment or retaliation?
What does the policy say about expense receipts?
What is the CEO home address?
```

The final question is intentionally unsupported and should trigger the safe fallback path.

---

## Expected Supported Behavior

Example question:

```text
What is the remote work equipment allowance?
```

Expected system behavior:

- supporting evidence is retrieved
- evidence status is moderate or strong
- confidence is greater than zero
- a citation points to the relevant policy section and page
- the configured provider generates the answer
- fallback is `false`

The generated answer should remain limited to information supported by the retrieved policy evidence.

---

## Expected Unsupported Behavior

Example question:

```text
What is the CEO home address?
```

Expected system behavior:

- evidence status is insufficient
- no normal answer is generated
- confidence is `0.0`
- citation count is `0`
- provider is reported as unavailable or none for the fallback path
- fallback is `true`

This demonstrates that the system does not invent unsupported policy details.

---

## Trust and Safety Design

PolicyGPT follows these core rules:

1. Answers should be grounded in uploaded documents.
2. Generation should be skipped when evidence is insufficient.
3. Citations should expose the evidence used to support the answer.
4. Missing evidence should be communicated explicitly.
5. API keys should never be returned through the UI or health endpoint.
6. Users should treat results as decision support and verify important policy interpretations with the document owner.

### Current safety boundaries

PolicyGPT:

- does not provide legal advice
- does not replace HR, compliance, privacy, or legal professionals
- does not verify whether an uploaded policy is current or officially approved
- does not guarantee that retrieval found every relevant passage
- does not automatically make employment or compliance decisions
- should not receive confidential organizational files without an approved secure deployment

---

## Validation and Demonstration

The current repository includes:

- interactive Swagger documentation
- a fictional demonstration PDF
- supported and unsupported example questions
- a manual smoke-test checklist
- UI screenshots covering ingestion, supported answers, fallback, evidence inspection, architecture, and backend endpoints

Formal RAG evaluation is not yet complete. The project does not currently claim measured retrieval accuracy, faithfulness, hallucination rate, or production reliability.

---

## Current Limitations

- Phase 1 MVP
- no user authentication
- no role-based access control
- no encrypted multi-user document store
- no PostgreSQL metadata database
- no document deletion endpoint
- no formal RAG evaluation dataset
- no automated retrieval or faithfulness scorecard
- no OCR for scanned PDFs
- no multi-document comparison
- no production monitoring
- no production cloud deployment
- no legal or compliance validation

---

## Roadmap

### Phase 2 — Evaluation and Platform Foundations

- create a labelled policy-question evaluation set
- measure retrieval relevance and citation quality
- evaluate answer faithfulness
- add confidence analytics
- add PostgreSQL metadata storage
- add Docker Compose
- add structured latency, score, token, and cost logging
- add automated backend tests
- add GitHub Actions CI

### Phase 3 — Advanced Document Intelligence

- multi-document comparison
- policy-version comparison
- compliance-summary generation
- human-reviewed report export
- LangGraph query routing where justified
- authentication and RBAC
- secure cloud deployment
- observability and operational dashboards

---

## Engineering Skills Demonstrated

This project demonstrates practical experience with:

- end-to-end RAG system design
- PDF extraction and preprocessing
- metadata-aware chunking
- SentenceTransformer embeddings
- ChromaDB vector retrieval
- retrieval-score thresholds
- evidence-gated generation
- citation construction
- provider abstraction
- safe fallback behavior
- FastAPI backend architecture
- Pydantic request and response contracts
- modular service design
- Streamlit product-interface development
- failure-state and empty-state UX
- environment-based configuration
- responsible AI boundaries
- production-readiness planning

---

## Accuracy and Honesty

The README separates implemented functionality from planned work.

PolicyGPT currently demonstrates a working Phase 1 evidence-first RAG workflow. Formal RAG evaluation, authentication, PostgreSQL metadata storage, Docker Compose, CI/CD, monitoring, and cloud deployment remain future work.

No unsupported accuracy, hallucination-reduction, compliance, or production-readiness claims are made.

---

## Author

**Chintan Patel**

- [Portfolio](https://chintan-patel-ai.netlify.app/)
- [LinkedIn](https://www.linkedin.com/in/chintan-patel-ai/)
- [GitHub](https://github.com/chintan-02)

---

## License and Use

This project is intended for portfolio, educational, research, and software-engineering demonstration purposes.

It should not be used as an official HR, legal, policy, or compliance decision system without the security, evaluation, governance, and organizational controls described above.
