# PolicyGPT Next.js product

This directory contains the production frontend for PolicyGPT Enterprise: a Next.js 16 / React 19 application covering Documents, Ask, Evaluation, and System workflows.

It is not a static mock and it does not connect to FastAPI from browser code. Server Components and Route Handlers form a Backend-for-Frontend (BFF) that owns the upstream URL, bounded timeouts, no-store requests, runtime validation, request-ID forwarding, and safe error normalization.

## Runtime architecture

```text
browser
→ Next.js pages and client interactions
→ /api/* Route Handlers (server-side BFF)
→ FASTAPI_URL (server-only)
→ FastAPI evidence API
```

`FASTAPI_URL` must never use a `NEXT_PUBLIC_` prefix. Production startup fails safely when it is absent. Browser-safe identity labels use explicit `NEXT_PUBLIC_APP_*` variables.

Console routes are dynamically rendered because live backend state is unavailable during image construction and must not be prerendered into the release image.

## Product areas

- **Documents:** PostgreSQL-backed registry, filename search, status filters, offset pagination, PDF upload, duplicate state, lifecycle polling, and safe detail views.
- **Ask:** real evidence-gated question flow, supported and unsupported presentations, page provenance, confidence diagnostics, and citation-only provider fallback.
- **Evaluation:** latest-run overview, cases, confidence, provider reliability, and read-only JSON/CSV downloads.
- **System:** frontend state, backend liveness, backend readiness, PostgreSQL, Chroma, provider mode, last-checked time, refresh, and controlled degraded/unavailable states.

## Readiness integration

`GET /api/health` proxies the lightweight FastAPI liveness contract.

`GET /api/ready` calls FastAPI `/api/v1/ready` server-side with a three-second timeout. The response is validated with Zod and normalized into PostgreSQL, Chroma, and answer-provider states. A backend 503 remains a safe public 503; malformed output, timeouts, and configuration failures become controlled unknown/unavailable states. Internal URLs, Compose names, credentials, and backend exception text are never returned.

The System page distinguishes:

- **Operational:** required evidence services and configured generation are available.
- **Degraded:** PostgreSQL and Chroma are ready while citation-only fallback is active.
- **Unavailable:** backend readiness cannot be verified or a required dependency is down.

The provider card reports configuration/fallback mode only. It does not make a paid provider request.

## Security headers

`next.config.ts` disables `X-Powered-By` and applies:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- a conservative `Permissions-Policy`
- `Cross-Origin-Opener-Policy: same-origin`

HSTS is intentionally absent for local HTTP. A strict CSP is deferred until scripts, fonts, uploads, and all current flows can be validated end-to-end.

## Data and error contracts

Generated OpenAPI types live in `src/lib/api/generated.ts`. Runtime boundary validation uses Zod because generated TypeScript types do not validate network data.

BFF routes return user-safe errors and disable caching for live data. They do not forward raw upstream error bodies. The Ask BFF propagates a safe backend request ID when available; the readiness BFF accepts and forwards only a conservative request-ID format.

## Standalone Docker build

The Dockerfile uses dependency, builder, and runtime stages. `output: "standalone"` produces the minimal server bundle. The runtime image uses a non-root `nextjs` user and contains public/static assets plus the standalone server.

Compose sets `FASTAPI_URL=http://backend:8000` only inside the frontend container and gates frontend health on `/api/ready`.

## Local development

```bash
npm ci
cp .env.local.example .env.local
npm run dev
```

The native development fallback is `http://localhost:8000`; production requires `FASTAPI_URL` explicitly.

## Validation

```bash
npm run lint
npm run test
npm run build
```

The current suite covers runtime schemas, domain adapters, evidence/answer presentation, document state, evaluation selectors, System operational mapping, and readiness BFF normalization. Tests never call a real backend.

Regenerate OpenAPI types after an intentional backend contract change while FastAPI is running:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/generated.ts
```

## Responsive and accessibility principles

- semantic headings, landmarks, tables, lists, labels, and status text
- keyboard-operable controls and visible focus behavior from the shared design system
- status communicated with text/icons as well as color
- responsive registry, details, evidence, and evaluation layouts
- no invented progress percentages, availability metrics, or provider reachability
- engineering details remain secondary to outcome and evidence

Authentication, dark mode, chat history, streaming, document-scoped Ask, delete/reindex, and fake analytics are intentionally outside this frontend release.
