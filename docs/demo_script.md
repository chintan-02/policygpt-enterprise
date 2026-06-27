# PolicyGPT Enterprise Demo Script

Use this script when presenting PolicyGPT Enterprise to a recruiter, instructor, class, or interviewer.

The goal of the demo is to show that PolicyGPT is not a simple PDF chatbot. It is a production-shaped RAG assistant with evidence retrieval, confidence scoring, citations, fallback behavior, and provider-agnostic LLM generation.

---

## 1. Short Introduction

PolicyGPT Enterprise is a Retrieval-Augmented Generation assistant for HR, SOP, policy, and compliance documents.

Users upload policy PDFs and ask natural-language questions. The system retrieves relevant document evidence first, checks whether the evidence is strong enough, and only then generates an answer.

Every answer includes citation cards with page-level evidence. When the system cannot find enough evidence, it does not guess. It returns a safe fallback message.

---

## 2. Thirty-Second Pitch

Use this version when you need to explain the project quickly:

> PolicyGPT Enterprise is a production-style RAG assistant for HR and compliance documents. It allows users to upload policy PDFs and ask questions, but it does not blindly call an LLM. It first retrieves page-level evidence, scores the evidence, filters weak matches, and only generates an answer when supporting evidence exists. The UI shows confidence, provider used, fallback status, retrieval trace, and citation cards.

---

## 3. What Makes It Different

Most PDF chatbot demos follow this pattern:

```text
Upload PDF
→ retrieve chunks
→ ask LLM to answer
```

PolicyGPT Enterprise follows a safer enterprise pattern:

```text
Upload PDF
→ extract text
→ clean text
→ create chunks with metadata
→ generate embeddings
→ store in ChromaDB
→ retrieve evidence
→ score evidence
→ apply threshold
→ generate only if supported
→ return answer + confidence + citations
```

This matters because HR, SOP, and compliance answers must be grounded. A wrong or unsupported answer can create business risk.

---

## 4. Demo Setup

Before the demo, run the backend:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Then run the Streamlit UI in a second terminal:

```bash
streamlit run ui/app.py
```

Open the UI:

```text
http://localhost:8501
```

Use the sample document:

```text
examples/sample_hr_policy.pdf
```

For a clean demo, remove previous local vector data before starting:

```bash
rm -rf data/chroma
```

Then restart the backend and upload the sample PDF once.

---

## 5. Demo Flow

### Step 1 — Show the FastAPI Backend

Open:

```text
http://localhost:8000/docs
```

Say:

> This is the FastAPI backend. It exposes endpoints for PDF upload, evidence retrieval, raw semantic search, and citation-backed question answering.

Point out these endpoints:

| Endpoint                     | Purpose                         |
| ---------------------------- | ------------------------------- |
| `/api/v1/health`             | Backend health check            |
| `/api/v1/documents/upload`   | Upload and index a PDF          |
| `/api/v1/documents/search`   | Raw semantic search             |
| `/api/v1/documents/evidence` | Retrieve citation evidence      |
| `/api/v1/documents/ask`      | Generate citation-backed answer |

Explain:

> The route handlers are intentionally thin. Business logic is separated into service files for extraction, cleaning, chunking, embeddings, retrieval, vector storage, and answer generation.

---

### Step 2 — Show the Streamlit Console

Open:

```text
http://localhost:8501
```

Say:

> The frontend is designed as a Compliance Intelligence Console, not a chatbot clone. It exposes the trust signals behind the RAG system: backend status, document ingestion, evidence status, confidence score, LLM provider, fallback status, retrieval trace, and citation cards.

Point out:

* backend connected card
* document ingestion panel
* policy question input
* demo question buttons
* answer card
* evidence badge
* confidence badge
* provider badge
* fallback badge
* retrieval trace
* citation cards

---

### Step 3 — Upload the Sample HR Policy PDF

Upload:

```text
examples/sample_hr_policy.pdf
```

Expected upload result:

* pages: 12
* chunks: around 20
* stored chunks: around 20
* collection: `policygpt_documents`

Say:

> When the PDF is uploaded, the backend extracts text page by page, cleans PDF extraction noise, creates metadata-rich chunks, generates embeddings, and stores them in ChromaDB.

Explain the ingestion pipeline:

```text
PDF upload
→ PyMuPDF extraction
→ text cleaning
→ page-aware chunking
→ embeddings
→ ChromaDB storage
```

---

### Step 4 — Ask a Supported Policy Question

Ask:

```text
What is the remote work equipment allowance?
```

Expected answer should mention:

* one-time equipment allowance
* up to CAD 300
* approved ergonomic or productivity items
* receipts required
* approval before reimbursement

Say:

> This answer is generated only because the retrieval layer found supporting evidence above the threshold. The citation card shows the source document, page number, section title, excerpt, and retrieval score.

Point out:

* Evidence: Moderate or Strong
* Confidence score greater than 0
* Provider: Groq or OpenAI
* Fallback: False
* Citation card points to page 5
* Section title: Remote and Hybrid Work

---

### Step 5 — Ask an AI Policy / Data Privacy Question

Ask:

```text
Can employees paste confidential data into public AI tools?
```

Expected answer:

Employees must not paste confidential information, personal data, customer data, proprietary code, internal documents, or security details into public AI tools unless the tool has been approved by Security and Legal for that data category.

Say:

> This question demonstrates a compliance-relevant use case. The answer is not based on general AI knowledge. It is grounded in the uploaded HR policy.

Point out:

* evidence status should be strong or moderate
* citation should point to the Confidentiality, Data Privacy, and AI Tool Use section
* answer should include Security and Legal approval
* fallback should be false

---

### Step 6 — Ask an Unsupported Question

Ask:

```text
What is the CEO home address?
```

Expected result:

* no generated answer
* evidence status: insufficient
* confidence score: 0.0
* citation count: 0
* provider: none
* fallback: true

Say:

> This is the most important safety behavior. The document does not contain the CEO home address, so the system does not invent one. It skips LLM generation and returns a fallback response.

This proves:

* retrieval gating works
* hallucination risk is reduced
* unsupported answers are handled safely
* the LLM is not called when evidence is insufficient

---

### Step 7 — Show Evidence Explorer

Open the **Evidence Explorer** page.

Ask:

```text
What is the remote work equipment allowance?
```

Say:

> This page separates retrieval from generation. It helps debug whether the system is finding the right evidence before calling the LLM.

Point out:

* evidence status
* confidence score
* retrieval threshold
* generation allowed flag
* citation cards
* retrieval trace
* page number and section title

Explain:

> This is useful because production RAG systems need observability. We need to know what evidence was retrieved, not only what the LLM answered.

---

### Step 8 — Show Architecture Page

Open the **Architecture** page.

Say:

> This page explains the full system flow from PDF upload to citation-backed answer generation.

Walk through:

```text
PDF Upload
→ Text Extraction
→ Cleaning
→ Chunking with Metadata
→ Embeddings
→ ChromaDB
→ Retrieval
→ Evidence Scoring
→ LLM Provider
→ Citation-Backed Answer
```

Mention:

> I intentionally kept agents, auth, PostgreSQL, and evaluation out of Phase 1 because the first priority was to ship a working RAG pipeline.

---

## 6. Technical Explanation

PolicyGPT uses:

| Layer             | Technology                      |
| ----------------- | ------------------------------- |
| Backend API       | FastAPI                         |
| Schema validation | Pydantic v2                     |
| PDF extraction    | PyMuPDF                         |
| Embeddings        | SentenceTransformers            |
| Vector database   | ChromaDB                        |
| LLM provider      | Groq / OpenAI / no-LLM fallback |
| Frontend          | Streamlit                       |
| UI architecture   | Modular components and pages    |

Backend flow:

```text
PDF upload
→ extract page text
→ clean text
→ infer section titles
→ create chunks with metadata
→ embed chunks
→ store vectors in ChromaDB
→ embed user query
→ retrieve candidate chunks
→ filter by score threshold
→ create citation cards
→ generate answer only if evidence passes
```

---

## 7. Strong Interview Explanation

Use this explanation:

> I built PolicyGPT Enterprise as a production-shaped RAG assistant for HR and compliance documents. The system does not blindly call an LLM. It first retrieves page-level evidence from uploaded PDFs, scores the evidence, filters weak matches, and only generates an answer when supporting evidence exists. The UI shows confidence, evidence status, provider used, fallback status, retrieval trace, and citation cards with page-level excerpts.

---

## 8. Why Provider-Agnostic Design Matters

Say:

> I designed the LLM layer so it can use Groq, OpenAI, or no-LLM fallback mode. This keeps development cost low with Groq, but still allows OpenAI to be swapped in later. It also shows that retrieval and answer generation are decoupled.

This is stronger than saying:

> I connected OpenAI to a PDF chatbot.

A better portfolio line is:

> Built a provider-agnostic RAG assistant with evidence-gated generation, citation-backed answers, Groq/OpenAI support, confidence scoring, and safe fallback behavior.

---

## 9. Current Limitations

Be honest if asked:

* The current version does not include authentication yet.
* It does not use PostgreSQL metadata yet.
* It does not support OCR scanned PDFs yet.
* It does not support multi-document comparison yet.
* Evaluation dashboard is planned for Phase 2.
* It is currently a local MVP, not a deployed production system.

Then say:

> I intentionally focused on shipping the working RAG pipeline first before adding production features like auth, metadata storage, evaluation, and deployment.

---

## 10. Closing Statement

End the demo with:

> PolicyGPT Enterprise shows the full RAG workflow: document ingestion, vector retrieval, evidence scoring, citation-backed generation, and safe fallback behavior. The goal was to build something closer to an enterprise document intelligence product rather than a simple chatbot demo.
