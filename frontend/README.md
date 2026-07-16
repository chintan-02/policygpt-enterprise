# PolicyGPT Enterprise frontend

PolicyGPT Enterprise — Evidence Intelligence Console is the product interface for a governed document-intelligence system that answers enterprise policy questions only when supporting evidence is available.

> Ask a policy question. Verify the answer. Trace every claim.

## Technology

- Next.js 16 App Router and React Server Components
- React 19 and TypeScript
- Tailwind CSS v4 with centralized CSS tokens
- shadcn Base Nova primitives backed by Base UI
- Lucide icons
- Geist Sans for interface copy and Geist Mono for traceability metadata

## Phase 14C scope

Phase 14C adds a production-facing, read-only evaluation product while preserving the Phase 14B Ask workflow. Evaluation pages read the latest generated artifact through FastAPI and server-only Next.js adapters; browser downloads use same-origin BFF routes.

The evaluation product separates evidence retrieval, unsupported-answer safety, answer completeness, calibrated confidence, provider availability, and request failures. It never runs the benchmark, invents metrics, or reads backend files from the browser.

## Environment setup

Copy the example file and adjust local values if necessary:

```bash
cp .env.local.example .env.local
```

`FASTAPI_URL` is server-only and must never use the `NEXT_PUBLIC_` prefix. Production deployments must set it explicitly.

Start the backend from the repository root:

```bash
cd ..
source .venv/bin/activate
python -m uvicorn app.api.main:app \
  --reload \
  --reload-dir app \
  --host 0.0.0.0 \
  --port 8000
```

Start the frontend:

```bash
cd frontend
npm run dev
```

## Route map

| Route | Phase 14C state |
| --- | --- |
| `/` | Overview with live backend health |
| `/documents` | Honest persistence placeholder |
| `/ask` | Live citation-backed Ask workspace |
| `/evaluations/overview` | Real-data quality outcomes and production gates |
| `/evaluations/cases` | Filterable TanStack case table and URL-selected detail drawer |
| `/evaluations/confidence` | Calibrated confidence and guardrail interpretation |
| `/evaluations/provider` | Generation availability and citation-only fallback diagnostics |
| `/evaluations/runs/latest` | Latest run metadata and JSON/CSV downloads |
| `/system` | Live health, architecture, and capability boundaries |
| `/api/health` | Safe Next.js health BFF response |
| `/api/ask` | Validated same-origin Ask BFF endpoint |
| `/api/evaluations/latest` | Safe latest-evaluation JSON BFF/download |
| `/api/evaluations/latest.csv` | Preserved latest-evaluation CSV BFF/download |

`/evaluations` redirects to `/evaluations/overview`. Evaluation navigation uses real URLs, so every route can load directly.

## Evaluation data flow

Generate and validate artifacts from the repository root:

```bash
python eval/validate_dataset.py
python eval/run_eval.py --request-delay-seconds 5
```

FastAPI exposes the configured, repository-contained artifact through:

- `GET /api/v1/evaluations/latest`
- `GET /api/v1/evaluations/latest.csv`

The JSON summary remains the source of truth for official aggregate metrics. Frontend selectors derive only presentation counts, diagnostic categories, provider availability, filters, and chart groupings. Generated JSON/CSV artifacts are ignored by Git and should be regenerated per environment.

When fewer cases are present than the available benchmark dataset, the UI labels the artifact a diagnostic run. Runs with fewer than three cases show compact case diagnostics instead of misleading distribution charts. Citation-only provider fallback is amber and does not reduce retrieval or safety gates when their structured outcomes passed.

Confidence is calibrated from retrieval strength, question coverage, evidence separation, numeric consistency, and scope guardrails. It is not an LLM self-rating, and raw retrieval scores remain decimals rather than percentages.

The Streamlit evaluation dashboard remains the internal QA console. Persistent PostgreSQL evaluation history is intentionally pending.

## Design-system rules

- No gradients, glow, glassmorphism, purple, chatbot bubbles, or decorative AI motifs.
- Color, spacing, radius, and motion values are centralized in `src/styles/tokens.css`.
- White, border-led surfaces sit on the `#F6F8FB` application background.
- Geist Mono and tabular numerals are reserved for numeric and traceability data.
- State always includes readable text; color is never the only signal.
- Retrieval similarity remains a raw decimal and is never converted into a percentage.
- The provenance rail is the signature source-traceability pattern.

## Ask request flow

1. The browser validates a non-empty question up to 2,000 characters.
2. `POST /api/ask` applies the same validation, uses a 60-second upstream timeout, and sends only the question plus the backend default retrieval count.
3. FastAPI retrieves and calibrates evidence, then returns a structured supported, unsupported, or provider-fallback response.
4. A supported answer is presented only when at least one citation is present. Retrieval scores remain raw decimals; only the calibrated confidence score is displayed as a percentage.

Ask searches all documents currently indexed in the evidence store. There is no document selector or persistent document library in this phase.

Supported responses show the grounded answer, a source/page summary, calibrated evidence confidence, decision reasons, the real citation metadata in the Provenance Rail, and a review disclaimer. Unsupported responses do not show speculative answer text. If evidence is answer-ready while the configured answer provider is unavailable, the workspace shows an amber citation-only fallback and preserves the available evidence.

The Provenance Rail traces each excerpt to its safe document name, page, section, and support state. Retrieval similarity is shown only as a raw decimal inside collapsed engineering details; it is not a probability and is never formatted as a percentage.

## Manual sample questions

With the sample HR policy indexed:

- Supported or citation-only fallback: `What is the remote work equipment allowance, and what is required for reimbursement?`
- Unsupported: `What severance amount does Alberta law require for an employee with five years of service?`

The unsupported question must not produce external legal advice. Ask is synchronous in Phase 14B; streaming and SSE are explicitly deferred.

## Completed and pending workflows

The backend already supports PDF extraction and indexing, ChromaDB retrieval, grounded generation, page-level citations, calibrated confidence, safety guardrails, observability, evaluation, provider retries, and safe citation-only fallback.

Phase 14C does not add uploads, document persistence, persistent evaluation history, streaming, PostgreSQL, authentication, roles, multi-tenancy, dark mode, or agent behavior. There is intentionally no authentication in this phase; no production authorization claim is implied.

## Verification

```bash
npm test
npm run lint
npm run build
```

Regenerate the frontend contract after an intentional FastAPI schema change while the backend is running:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/generated.ts
```
