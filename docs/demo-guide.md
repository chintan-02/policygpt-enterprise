# Recruiter and interview demo guide

## Before the call

1. Start Compose and run `scripts/compose/smoke-test.sh`.
2. Confirm the sample HR policy is indexed once and record its document detail URL.
3. Open Documents, Ask, Evaluation overview, Evaluation cases/confidence, and System in separate tabs.
4. Keep `/docs` available for the engineering walkthrough.
5. If demonstrating provider fallback, use an intentionally empty key or `LLM_PROVIDER=none`; never break required dependencies.

Use only real application output. Do not quote evaluation metrics that are not visible in the validated artifact.

## 90-second recruiter demo

**0:00–0:15 — Documents.** Open `/documents`. “PolicyGPT is an evidence-first policy RAG product. PDFs become durable records with PostgreSQL identity, source storage, and Chroma evidence.”

**0:15–0:40 — Ask.** Open `/ask` and ask: `What is the remote work policy?` Show the supported answer, page citation, section/excerpt, confidence, and provider/fallback label. “The model is downstream of an evidence gate; the answer remains traceable to the source.”

**0:40–0:58 — Unsupported.** Ask: `What is the CEO's private home address?` Show evidence rejection or the safe unsupported state. “No supporting policy evidence means no invented answer.”

**0:58–1:15 — Evaluation.** Open `/evaluations/overview`. Show that supported and unsupported behavior is evaluated from a checked-in dataset.

**1:15–1:30 — System.** Open `/system`. Show liveness, readiness, PostgreSQL, Chroma, and provider mode. Close with: “This is more than a PDF chatbot because it treats identity, evidence, failure, and deployment as product requirements.”

## Three-minute engineering demo

1. **Documents registry (35 seconds):** show lifecycle metadata and duplicate protection. Re-upload the same sample PDF and show the existing record is returned rather than indexed twice.
2. **Supported Ask (40 seconds):** ask `What is the remote work policy?`; point to page provenance and calibrated confidence, not just generated prose.
3. **Unsupported Ask (30 seconds):** ask the private-address question; explain that the evidence gate prevents generation.
4. **Provider fallback (30 seconds):** with no provider key, repeat the supported question. Show that citations remain and the UI says citation-only fallback rather than claiming generation.
5. **Evaluation (25 seconds):** show overview, cases, and confidence diagnostics from the real latest artifact.
6. **System (20 seconds):** show required dependencies ready and provider mode degraded/operational independently.

## Seven-minute technical interview walkthrough

### Minute 0–1: problem and product

Open Documents. Explain the risk of fluent, untraceable policy answers and the requirement for persistent document identity, duplicate prevention, and lifecycle state.

### Minute 1–2: ingestion architecture

Use the README Mermaid diagram. Walk through PDF validation, SHA-256, atomic source storage, PostgreSQL lifecycle, page extraction/cleaning, metadata-aware chunks, local embeddings, and Chroma persistence.

### Minute 2–3: evidence and confidence

Open Ask with the supported question. Explain candidate retrieval, lexical/numeric/direct-support checks, external-authority scope risk, the answerability decision, and why similarity is not displayed as probability.

### Minute 3–4: unsupported and provider failure

Run the unsupported question. Then show citation-only fallback for the supported question. Distinguish these states: unsupported means evidence rejected; provider fallback means evidence passed but generation was not available.

### Minute 4–5: persistence and evaluation

Show the document UUID/detail and Evaluation cases. Explain PostgreSQL/Chroma/source ownership and the 16-question supported/unsupported benchmark. Avoid presenting benchmark metrics as production claims.

If demonstrating regeneration, start it explicitly from the repository root
with `bash scripts/evaluation/run-compose-eval.sh`, then use the Overview
“Refresh evaluation” action. The browser reads the completed artifact; it does
not execute the benchmark runner.

### Minute 5–6: operations

Open System. Explain process liveness versus PostgreSQL/Chroma readiness, the non-blocking provider policy, request IDs, safe logs/errors, security headers, migration gate, non-root containers, and named volumes.

### Minute 6–7: tradeoffs and roadmap

State the limits clearly: synchronous ingestion, embedded Chroma, local storage, no auth/tenancy/TLS/managed secrets/cloud backups. Explain that authenticated boundaries and durable asynchronous ingestion would precede scale work.

Close: “PolicyGPT demonstrates that trustworthy RAG is a system design problem—evidence, identity, evaluation, failure semantics, and operations—not only a prompt.”

## Exact demonstrations

### Supported question

`What is the remote work policy?`

Expected: answer-ready evidence with at least one real page citation, followed by generated text or a truthful citation-only fallback.

### Unsupported question

`What is the CEO's private home address?`

Expected: evidence rejection or safe unsupported response. Never narrate a guessed answer.

### Duplicate upload

On Documents, upload `examples/sample_hr_policy.pdf` a second time. Expected: the response identifies the existing document UUID and does not create another vector index.

### Provider-unavailable fallback

Use `LLM_PROVIDER=none` or an empty key, restart the backend normally, and verify readiness remains ready. Ask the supported question. Expected: evidence cards remain visible and answer generation is labeled citation-only fallback.

### System readiness

Show `/system`, then optionally the public `/api/ready` JSON. Explain that the System page performs no paid provider probe and exposes no connection details.

## Architecture explanation

“The browser talks to a Next.js BFF. FastAPI owns the RAG and metadata contracts. PostgreSQL owns identity and lifecycle, source storage owns PDFs, and Chroma owns chunks/vectors. Retrieval and confidence decide whether generation is allowed. Groq/OpenAI is optional; evidence remains useful without it. Compose gates startup on migrations and required dependency readiness.”

## Closing summary

“The differentiator is controlled evidence behavior: durable document identity, metadata-aware retrieval, page provenance, calibrated answerability, unsupported handling, provider resilience, evaluation, request tracing, and release-like deployment. It is deliberately honest about the controls still required for cloud production.”
