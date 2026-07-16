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

## Phase 14B scope

This phase connects the real Ask PolicyGPT vertical slice to the existing FastAPI retrieval and answer pipeline. The browser calls the same-origin `POST /api/ask` route, which validates the request and forwards it server-side to `POST /api/v1/documents/ask`.

The Ask workspace presents supported answers with citations, unsupported outcomes, provider fallback, request failures, and invalid responses as distinct states. It does not infer state from answer text.

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

| Route | Phase 14B state |
| --- | --- |
| `/` | Overview with live backend health |
| `/documents` | Honest persistence placeholder |
| `/ask` | Live citation-backed Ask workspace |
| `/evaluations/overview` | Evaluation overview placeholder |
| `/evaluations/cases` | Case inspection placeholder |
| `/evaluations/confidence` | Confidence calibration placeholder |
| `/evaluations/provider` | Provider reliability placeholder |
| `/evaluations/runs/latest` | Latest-run placeholder |
| `/system` | Live health, architecture, and capability boundaries |
| `/api/health` | Safe Next.js health BFF response |
| `/api/ask` | Validated same-origin Ask BFF endpoint |

`/evaluations` redirects to `/evaluations/overview`. Evaluation navigation uses real URLs, so every route can load directly.

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

Phase 14B does not add uploads, document persistence, evaluation reporting, streaming, PostgreSQL, authentication, roles, multi-tenancy, dark mode, or agent behavior. There is intentionally no authentication in this phase; no production authorization claim is implied.

## Verification

```bash
npm test
npm run lint
npm run build
```

Regenerate the frontend contract after an intentional FastAPI schema change:

```bash
cd ..
python scripts/export_openapi.py
npx openapi-typescript openapi.json -o frontend/src/lib/api/generated.ts
```
