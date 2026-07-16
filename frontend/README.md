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

## Phase 14A scope

This phase establishes the application shell, responsive navigation, route structure, PolicyGPT design system, server-only FastAPI health access, honest operational states, and reusable evidence UI primitives. The existing FastAPI backend remains unchanged.

The Streamlit application remains the internal QA console. This Next.js application is the product foundation.

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

| Route | Phase 14A state |
| --- | --- |
| `/` | Overview with live backend health |
| `/documents` | Honest persistence placeholder |
| `/ask` | Honest Phase 14B integration placeholder |
| `/evaluations/overview` | Evaluation overview placeholder |
| `/evaluations/cases` | Case inspection placeholder |
| `/evaluations/confidence` | Confidence calibration placeholder |
| `/evaluations/provider` | Provider reliability placeholder |
| `/evaluations/runs/latest` | Latest-run placeholder |
| `/system` | Live health, architecture, and capability boundaries |
| `/api/health` | Safe Next.js health BFF response |

`/evaluations` redirects to `/evaluations/overview`. Evaluation navigation uses real URLs, so every route can load directly.

## Design-system rules

- No gradients, glow, glassmorphism, purple, chatbot bubbles, or decorative AI motifs.
- Color, spacing, radius, and motion values are centralized in `src/styles/tokens.css`.
- White, border-led surfaces sit on the `#F6F8FB` application background.
- Geist Mono and tabular numerals are reserved for numeric and traceability data.
- State always includes readable text; color is never the only signal.
- Retrieval similarity remains a raw decimal and is never converted into a percentage.
- The provenance rail is the signature source-traceability pattern.

## Completed and pending workflows

The backend already supports PDF extraction and indexing, ChromaDB retrieval, grounded generation, page-level citations, calibrated confidence, safety guardrails, observability, evaluation, provider retries, and safe citation-only fallback.

Phase 14A does not add Ask API integration, upload, document persistence, evaluation reporting, streaming, PostgreSQL, authentication, roles, multi-tenancy, or dark mode. There is intentionally no authentication in this foundation phase; no production authorization claim is implied.

## Verification

```bash
npm run lint
npm run build
```
