# PolicyGPT Enterprise

**PolicyGPT Enterprise** is a production-style Retrieval-Augmented Generation system for HR, policy, SOP, and compliance document intelligence.

Users upload policy PDFs and ask natural-language questions. The system retrieves document evidence first, checks retrieval confidence, and generates answers only when supporting evidence is available. Responses include citation cards, page-level evidence, confidence scoring, LLM provider visibility, and safe fallback behavior when evidence is weak.

This is not a generic PDF chatbot. It is designed as an enterprise-style **Compliance Intelligence Console** that prioritizes trust, evidence, and safe answer generation.

---

## Project Status

**Current phase:** Phase 2, Step 16 — Reproducible Docker Compose deployment

### Completed

* FastAPI backend
* PDF upload endpoint
* PDF text extraction with page-level metadata
* Text cleaning and PDF extraction repair
* Page-aware chunking with metadata
* Local embeddings using SentenceTransformers
* ChromaDB vector storage
* Semantic retrieval pipeline
* Evidence scoring and threshold filtering
* Citation card generation
* Unsupported-answer fallback
* Provider-agnostic LLM layer
* Groq / OpenAI / no-LLM fallback support
* Streamlit Compliance Intelligence Console
* Evidence Explorer page
* Architecture overview page
* README and demo documentation
* Clean citation preview formatting
* Professional empty, loading, and error UI states
* Backend health endpoint with safe RAG configuration details
* Verified RAG evaluation dataset and repeatable runner
* Explainable confidence calibration and safety guardrails
* Read-only Streamlit RAG Evaluation Dashboard
* Read-only Next.js evaluation product with overview, cases, confidence,
  provider reliability, and latest-run downloads
* Durable PostgreSQL document metadata with Alembic migrations
* Atomic local source-PDF storage and SHA-256 duplicate prevention
* Read-only document list, detail, and lifecycle-status APIs
* Real Next.js Documents registry, PDF upload, and document detail routes
* URL-backed filename search, status filters, and backend pagination
* Truthful ingestion lifecycle, duplicate, processing, failure, and outage states
* Reproducible four-service Docker Compose deployment with migration gating
* Non-root FastAPI and Next.js production images
* Persistent named volumes for PostgreSQL, ChromaDB, uploads, logs, and evaluations

### Planned Later

* Persistent evaluation history
* Multi-document comparison
* Compliance report generation
* Cloud deployment

---

## Screenshots

### Document Ingestion Console

The system shows backend connection status, PDF upload, document indexing, page count, chunk count, stored vector count, and ChromaDB collection name.

<img src="screenshots/01-dashboard-upload.png" alt="PolicyGPT document ingestion dashboard" width="900"/>

---

### Citation-Backed Answer

PolicyGPT retrieves evidence first, generates an answer only when evidence passes the threshold, and returns citation cards with page-level source information.

<img src="screenshots/02-citation-backed-answer.png" alt="PolicyGPT citation-backed answer with evidence score and citation card" width="900"/>

---

### AI Policy and Data Privacy Question

The system answers compliance-style questions about confidential data and AI tools using only uploaded policy evidence.

<img src="screenshots/03-ai-policy-answer.png" alt="PolicyGPT AI policy answer with strong evidence and citations" width="900"/>

---

### Unsupported Question Fallback

When the uploaded document does not contain enough supporting evidence, PolicyGPT skips generation and returns a safe fallback response.

<img src="screenshots/04-unsupported-fallback.png" alt="PolicyGPT unsupported question fallback with no citations" width="900"/>

---

### Evidence Explorer

The Evidence Explorer exposes the retrieval layer before generation, including evidence status, confidence score, threshold, retrieval trace, and retrieved citation cards.

<img src="screenshots/05-evidence-explorer.png" alt="PolicyGPT evidence explorer with retrieval trace and citation cards" width="900"/>

---

### Architecture Page

The architecture page explains the full RAG flow from PDF upload to citation-backed answer generation.

<img src="screenshots/06-architecture-page.png" alt="PolicyGPT architecture page showing RAG system flow" width="900"/>

---

### FastAPI Backend

The backend exposes documented API endpoints for health checks, document upload, semantic search, evidence retrieval, and question answering.

<img src="screenshots/07-fastapi-docs.png" alt="PolicyGPT FastAPI Swagger documentation" width="900"/>


## Why This Project Matters

Many RAG demos follow a simple pattern:

```text
Upload PDF
→ retrieve chunks
→ ask LLM to answer
```

That is useful for a prototype, but it is not enough for HR, compliance, SOP, or policy use cases where unsupported answers can create risk.

PolicyGPT Enterprise follows a safer enterprise RAG pattern:

```text
Question
→ retrieve evidence
→ score evidence
→ apply threshold
→ generate only if supported
→ return answer + confidence + citations
```

If the system cannot find enough supporting evidence, it does not guess. It returns a fallback response.

This makes the project more relevant for real-world document intelligence workflows where answers need to be grounded, auditable, and explainable.

---

## Key Features

### Citation-Backed Answers

Every generated answer is connected to citation cards containing:

* document name
* page number
* section title
* excerpt
* retrieval score

This makes the answer auditable instead of only conversational.

---

### Evidence-Gated Generation

The backend does not blindly call the LLM.

Before generation, the system:

1. Embeds the user question
2. Retrieves candidate chunks from ChromaDB
3. Filters chunks by retrieval score
4. Builds citation cards
5. Calculates evidence status and confidence
6. Allows generation only when evidence is available

If evidence is insufficient, PolicyGPT returns a safe fallback message instead of hallucinating.

---

### Provider-Agnostic LLM Layer

PolicyGPT supports multiple answer-generation modes:

* Groq
* OpenAI
* no-LLM fallback mode

This design keeps the project flexible. Groq can be used for fast and low-cost development demos, while OpenAI can be enabled later by changing environment variables.

The retrieval system is independent from the LLM provider.

---

### No-LLM Fallback Mode

If LLM generation is disabled, unavailable, rate-limited, or misconfigured, the system can still return citation evidence safely.

This prevents the UI from breaking during demos and shows production-style failure handling.

---

### Hidden LLM Evidence Text and Clean UI Excerpts

The backend separates long grounding text from short UI display text:

```text
evidence_text → longer hidden text for LLM grounding
excerpt       → shorter text for UI citation display
```

This gives the LLM enough context while keeping citation cards clean and readable for users.

---

### Enterprise-Style Streamlit UI

The frontend is designed as a **Compliance Intelligence Console**, not a chatbot clone.

The UI includes:

* backend connection status
* document ingestion panel
* policy question input
* answer card
* confidence badge
* evidence status badge
* provider badge
* model badge
* fallback badge
* retrieval trace
* citation cards
* Evidence Explorer page
* Architecture page

The goal is to show how the RAG system behaves, not just display an answer.

---

### Production-Style Polish

PolicyGPT includes small but important product-quality details:

* clean citation previews without noisy PDF boilerplate
* loading spinners during indexing, retrieval, and answer generation
* clear empty states before document upload
* clear state when a PDF is selected but not indexed
* friendly error messages for backend/API failures
* safe fallback state when no citation evidence is available
* backend health endpoint showing safe RAG configuration details
* API keys are never exposed through health checks or UI responses

These details make the project feel closer to an enterprise document intelligence product rather than a simple prototype.

---

## Enterprise UI Design

Most Streamlit AI apps look like this:

```text
Title
Textbox
Button
Answer
```

PolicyGPT uses a more structured product-style layout:

```text
Compliance Intelligence Console
├── Backend status
├── Document ingestion
├── Policy question panel
├── Evidence-gated answer card
├── Confidence and provider badges
├── Retrieval trace
└── Citation cards
```

The interface communicates trust signals clearly:

* Is the backend connected?
* Was the document indexed?
* Was evidence found?
* Did evidence pass the threshold?
* Was LLM generation allowed?
* Which provider generated the answer?
* Which document/page supports the answer?
* Did the system safely fall back?

This makes the demo stronger for AI Engineer, GenAI Developer, and LLM Engineer roles.

---

## Architecture

PolicyGPT Enterprise uses a modular RAG architecture.

```text
PDF Upload
→ PyMuPDF text extraction
→ text cleaning
→ page-aware chunking
→ SentenceTransformer embeddings
→ ChromaDB vector store
→ semantic retrieval
→ evidence score filtering
→ citation card creation
→ Groq/OpenAI/no-LLM answer generation
→ Streamlit UI
```

### High-Level Architecture

```text
User
  │
  ▼
Streamlit Compliance Console
  │
  ▼
FastAPI Backend
  │
  ├── PDF Upload
  ├── Text Extraction
  ├── Text Cleaning
  ├── Chunking
  ├── Embeddings
  ├── ChromaDB Storage
  ├── Evidence Retrieval
  ├── Confidence Scoring
  ├── Citation Builder
  └── LLM Answer Generation
          ├── Groq
          ├── OpenAI
          └── No-LLM Fallback
```

---

## System Design

PolicyGPT is separated into backend services and frontend components.

The backend follows a service-oriented structure. FastAPI route handlers stay thin and delegate business logic to service files.

### Backend Request Flow

#### Document Upload Flow

```text
POST /documents/upload
→ validate PDF
→ read file bytes
→ extract text with PyMuPDF
→ clean extracted page text
→ infer section titles
→ create chunks with metadata
→ generate embeddings
→ store chunks in ChromaDB
→ return ingestion summary
```

#### Evidence Retrieval Flow

```text
POST /documents/evidence
→ embed user query
→ search ChromaDB
→ filter results by retrieval score
→ remove duplicate citations
→ build citation cards
→ calculate confidence score
→ return evidence response
```

#### Question Answering Flow

```text
POST /documents/ask
→ retrieve evidence
→ check evidence status
→ if insufficient: return fallback
→ if supported: build LLM evidence context
→ call selected provider
→ return answer + citations + confidence
```

---

## Backend Service Responsibilities

| Service                   | Responsibility                                                             |
| ------------------------- | -------------------------------------------------------------------------- |
| `PDFExtractionService`    | Extract page-level text from uploaded PDFs                                 |
| `TextCleaningService`     | Clean extracted text and repair common PDF spacing issues                  |
| `ChunkingService`         | Create chunks while preserving document, page, section, and chunk metadata |
| `EmbeddingService`        | Generate local embeddings using SentenceTransformers                       |
| `VectorStoreService`      | Store and search vectors in ChromaDB                                       |
| `RetrievalService`        | Retrieve evidence, apply threshold filtering, create citation cards        |
| `AnswerGenerationService` | Generate citation-grounded answers using Groq/OpenAI or fallback           |
| `DocumentService`         | Orchestrate upload, retrieval, and answer workflows                        |

---

## Frontend Design

The Streamlit UI is organized into pages and reusable components.

### Pages

| Page              | Purpose                                               |
| ----------------- | ----------------------------------------------------- |
| Ask PolicyGPT     | Upload PDF, ask questions, view answers and citations |
| Evidence Explorer | Inspect retrieved citation evidence before generation |
| Architecture      | Explain the end-to-end RAG system design              |

### UI Components

| Component           | Purpose                                                           |
| ------------------- | ----------------------------------------------------------------- |
| `answer_card.py`    | Render generated answer or fallback response                      |
| `citation_card.py`  | Render document name, page, section, excerpt, and score           |
| `badges.py`         | Render evidence, confidence, provider, model, and fallback badges |
| `cards.py`          | Render reusable layout and summary cards                          |
| `evidence_panel.py` | Render retrieval trace and evidence summary                       |
| `styles.py`         | Apply custom enterprise-style CSS                                 |

---

## Tech Stack

### Backend

* Python
* FastAPI
* Pydantic v2
* PyMuPDF
* SentenceTransformers
* ChromaDB
* OpenAI Python SDK
* Groq OpenAI-compatible API
* structlog / Python logging

### Frontend

* Streamlit
* custom CSS
* reusable UI components
* multipage navigation
* session state
* requests API client

### Storage

* Local ChromaDB persistent directory
* PostgreSQL for durable document metadata
* Local `data/uploads` source-PDF storage
* Local `.env` configuration
* Demo PDF in `examples/`

---

## Folder Structure

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
│   │   ├── evaluation_components.py
│   │   └── evidence_panel.py
│   │
│   ├── services/
│   │   └── evaluation_results_service.py
│   │
│   └── pages/
│       ├── ask.py
│       ├── evidence.py
│       ├── evaluation_dashboard.py
│       └── architecture.py
│
├── docs/
│   ├── api_examples.md
│   ├── database.md
│   ├── demo_script.md
│   ├── docker-compose.md
│   └── smoke_test_checklist.md
│
├── frontend/
│   ├── Dockerfile
│   └── src/
│
├── scripts/
│   └── compose/
│       ├── import-local-data.sh
│       └── smoke-test.sh
│
├── examples/
│   └── sample_hr_policy.pdf
│
├── screenshots/
│   └── .gitkeep
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   └── chroma/
│
├── .env.example
├── .env.compose.example
├── compose.yaml
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Environment Variables

Create a `.env` file from `.env.example`.

Minimum local configuration:

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

DATABASE_URL=postgresql+psycopg://policygpt:change_me@localhost:5432/policygpt
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=5
DATABASE_POOL_TIMEOUT_SECONDS=30
DATABASE_ECHO=false
DOCUMENT_STORAGE_DIR=data/uploads

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

# Optional repository-relative dashboard result path
POLICYGPT_EVAL_RESULTS_PATH=eval/results/latest_eval_results.json
```

Do not commit your real `.env` file.

Compose uses a separate ignored `.env.compose` file. See
[Docker Compose local deployment](docs/docker-compose.md) for every setting,
persistence behavior, safe existing-volume reuse, and recovery procedures.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Run the complete stack with Docker Compose

Docker Compose is the reproducible local deployment path for the PostgreSQL,
migration, FastAPI, and Next.js services:

```bash
cp .env.compose.example .env.compose
# Replace the example database password before continuing.
docker compose --env-file .env.compose build
docker compose --env-file .env.compose up -d
scripts/compose/smoke-test.sh
```

The migration service must exit successfully before FastAPI starts. Named
volumes preserve application data across `docker compose down` and image
rebuilds. Do not use `down --volumes` unless a permanent reset is intended.
With a configured Groq or OpenAI key, supported questions can generate answers;
without a provider key, the existing citation-only fallback keeps retrieval and
evidence available safely.
The complete runbook is in [docs/docker-compose.md](docs/docker-compose.md).

---

## Run Backend

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend docs:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

---

## Run Streamlit UI

Open a second terminal:

```bash
source .venv/bin/activate
streamlit run ui/app.py
```

Open:

```text
http://localhost:8501
```

### RAG Evaluation Dashboard

The **RAG Evaluation** page is a read-only quality and observability view over:

```text
eval/results/latest_eval_results.json
eval/results/latest_eval_results.csv
```

Generate or refresh those artifacts outside Streamlit:

```bash
python eval/validate_dataset.py
python eval/run_eval.py --request-delay-seconds 5
```

Then start the existing UI entrypoint:

```bash
streamlit run ui/app.py
```

Use **Refresh results** in the dashboard after a new run. The optional
`POLICYGPT_EVAL_RESULTS_PATH` setting may point to another repository-relative
JSON artifact; browser users cannot choose arbitrary filesystem paths.

Partial runs remain viewable but are labeled clearly and should not be treated
as the full benchmark. Provider fallback is reported separately from retrieval
quality: an answer-ready case can retain correct citations while external
generation is replaced by the safe citation-only fallback. The dashboard does
not infer a specific provider error unless the artifact records one.

Generated JSON and CSV outputs are ignored by Git and should be regenerated in
each environment. The dashboard never runs the evaluator or reads provider logs.

---

## Demo PDF

A fictional sample HR policy PDF is included for testing:

```text
examples/sample_hr_policy.pdf
```

It is safe for public demo use and does not contain real employee data, confidential company information, or legal advice.

---

## Demo Questions

Try these questions after uploading the sample PDF:

```text
What is the remote work equipment allowance?
Can employees paste confidential data into public AI tools?
How many days in advance should employees request planned vacation?
What should employees do if they see harassment or retaliation?
What does the policy say about expense receipts?
What is the CEO home address?
```

The final question is intentionally unsupported and should trigger fallback behavior.

---

## Example Supported Response

Question:

```text
What is the remote work equipment allowance?
```

Expected behavior:

* answer is generated
* evidence status is moderate or strong
* confidence score is greater than zero
* citation card points to the remote/hybrid work section
* provider is Groq or OpenAI
* fallback is false

Expected answer should mention:

* one-time equipment allowance
* up to CAD 300
* approved ergonomic or productivity items
* receipts required
* approval before reimbursement

---

## Example Unsupported Response

Question:

```text
What is the CEO home address?
```

Expected behavior:

* no answer is generated
* evidence status is insufficient
* confidence score is 0.0
* citation count is 0
* provider is none
* fallback is true

This demonstrates that PolicyGPT does not invent unsupported policy details.

---

## API Endpoints

| Method | Endpoint                     | Purpose                         |
| ------ | ---------------------------- | ------------------------------- |
| `GET`  | `/api/v1/health`             | Check backend health            |
| `POST` | `/api/v1/documents/upload`   | Upload and index PDF            |
| `GET`  | `/api/v1/documents`          | List persistent document metadata |
| `GET`  | `/api/v1/documents/{id}`     | Read safe document metadata       |
| `GET`  | `/api/v1/documents/{id}/status` | Poll document lifecycle status |
| `POST` | `/api/v1/documents/search`   | Raw semantic search             |
| `POST` | `/api/v1/documents/evidence` | Retrieve citation evidence      |
| `POST` | `/api/v1/documents/ask`      | Generate citation-backed answer |

---

## Trust and Safety Design

PolicyGPT follows three safety rules:

1. Answers must be grounded in uploaded documents.
2. LLM generation is skipped when evidence is insufficient.
3. Citation cards expose the source evidence used for generation.

This helps reduce hallucination risk and makes the system more suitable for HR, SOP, compliance, and policy use cases.

---

## Current Limitations

This remains a local portfolio deployment rather than a hosted production
service.

Current limitations:

* no user authentication
* no role-based access control
* no document deletion endpoint yet
* no multi-document comparison yet
* no OCR for scanned PDFs yet
* no cloud-production deployment, TLS termination, or external secrets manager

These are intentionally deferred until after the core RAG flow is working.

---

## Roadmap

### Phase 1 — Core RAG MVP

* FastAPI backend
* PDF upload
* extraction
* cleaning
* chunking
* embeddings
* vector search
* citation-backed answers
* Streamlit UI

### Phase 2 — Differentiator

* RAG evaluation
* confidence analytics
* evaluation dashboard
* PostgreSQL metadata
* Docker Compose local deployment (complete)
* logging for latency, retrieval score, and token usage

### Phase 3 — Advanced

* multi-document comparison
* compliance report generation
* LangGraph query router
* cloud deployment
* CI/CD

---

## Portfolio Positioning

This project demonstrates:

* RAG system design
* FastAPI backend engineering
* vector search with ChromaDB
* citation-grounded answer generation
* LLM provider abstraction
* safe fallback behavior
* Streamlit dashboard UI
* production-style architecture thinking

Target roles:

* AI Engineer
* GenAI Developer
* LLM Engineer
* Machine Learning Engineer
* Data/AI Application Developer

---

## License

This project is for portfolio and educational use.
