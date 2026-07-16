# Deployment readiness

## Readiness statement

PolicyGPT Enterprise has a reproducible, release-like local Docker Compose deployment. It is suitable for portfolio demonstrations, engineering review, and controlled single-host evaluation. It is not described as cloud-production-ready.

## Implemented architecture

The stack uses PostgreSQL 16, a one-shot Alembic migration service, a non-root FastAPI container, and a non-root Next.js standalone container. Chroma, source PDFs, structured RAG logs, evaluation artifacts, and PostgreSQL data use stable named volumes.

Startup is gated in this order:

```text
postgres healthy → migrate exits 0 → backend ready → frontend ready
```

FastAPI owns ingestion, retrieval, evidence assessment, generation, and metadata APIs. Next.js owns the browser product and server-only BFF. PostgreSQL owns document identity and lifecycle metadata; Chroma owns indexed chunks and vectors; the uploads volume owns original PDF sources.

## Liveness and readiness

`GET /api/v1/health` proves only that FastAPI can serve a lightweight request. It does not access PostgreSQL, Chroma, embeddings, files, or answer providers.

`GET /api/v1/ready` performs two read-only checks:

- PostgreSQL: acquire an existing SQLAlchemy connection, execute `SELECT 1`, and close it.
- Chroma: access the configured collection and read its count without similarity search, embedding, or writes.

A failure returns HTTP 503 with only `ready` or `unavailable` dependency states. Connection URLs, hosts, ports, paths, and exception text are excluded.

Groq/OpenAI are optional dependencies. The endpoint reports whether answer generation is configured or citation-only fallback is active, but no paid provider call occurs and provider state never controls deployment readiness.

The Next.js `GET /api/ready` route calls FastAPI server-side with a bounded timeout, validates the response, disables caching, and returns a normalized public status. It never exposes `FASTAPI_URL` or Compose service names.

## Configuration and secrets

Copy `.env.compose.example` to ignored `.env.compose`. Replace the example PostgreSQL password. Provider keys may remain empty. Only `NEXT_PUBLIC_*` values enter browser-visible configuration; `FASTAPI_URL` is server-only.

Pydantic validates API prefix shape, ports and positive sizes, chunk overlap, ordered confidence thresholds, retry settings, provider choices, database scheme, storage/log paths, Chroma collection name, and CORS origins. It does not print secret values and does not require provider keys.

The project does not implement managed secrets. Operators are responsible for protecting `.env.compose`, restricting host access, rotating leaked credentials, and using an appropriate secret manager in a real deployment.

## Persistent data ownership and backup

| Asset | Owner | Default volume | Backup responsibility |
| --- | --- | --- | --- |
| Document identity/lifecycle | PostgreSQL | `policygpt_postgres_data` | database-consistent backup |
| Chunks and vectors | Chroma | `policygpt_chroma_data` | filesystem snapshot coordinated with metadata |
| Source PDFs | backend storage service | `policygpt_uploads_data` | file backup with access controls |
| RAG query logs | backend logger | `policygpt_logs_data` | retention and privacy policy |
| Evaluation artifacts | evaluation workflow | `policygpt_evaluation_results_data` | optional artifact retention |

PostgreSQL, Chroma, and source files form one logical dataset. A recoverable backup must preserve a consistent point across all three. Docker named volumes are persistence, not backups.

## Migration, release, rollback

Alembic is the only schema migration authority. The `migrate` service runs `alembic upgrade head` after PostgreSQL is healthy and must exit successfully before FastAPI starts.

Before release:

1. Back up persistent data.
2. Run `scripts/release/verify.sh`.
3. Review the migration and image changes.
4. Build images and start the stack.
5. Inspect `ps -a`, migration logs, and run the smoke test.

Rollback means restoring the previous application images and, if a schema change is incompatible, using a reviewed Alembic downgrade or restoring the coordinated backup. Do not assume an image rollback can safely reverse database changes. This release adds no schema migration.

## Failure behavior and recovery

| Failure | Expected behavior | Recovery |
| --- | --- | --- |
| PostgreSQL unavailable | liveness 200; readiness 503; Documents metadata unavailable | restore PostgreSQL, verify migrations, let health checks recover |
| Chroma unavailable | liveness 200; readiness 503; evidence workflows unavailable | restore Chroma volume/access, restart backend if needed, verify retrieval |
| Provider missing/unavailable | readiness remains ready; supported evidence uses citation-only fallback | configure provider or continue evidence-only operation |
| Backend unavailable | Next.js BFF returns a safe unavailable state without internal URL | restore backend, verify `/health` then `/ready` |
| Frontend unavailable | backend APIs may remain healthy | inspect frontend logs/config and restart frontend |
| Migration failure | backend and frontend do not enter healthy startup | inspect migration logs; correct config or migration deliberately |
| Source PDF missing | metadata/vector consistency is degraded; download is not exposed | restore the uploads backup; do not silently fabricate a source |

## Logging and request traceability

Each backend response has an `X-Request-ID`. Conservative inbound IDs are preserved; unsafe, multiline, or oversized values are replaced with UUIDs. One general HTTP completion log records request ID, method, normalized route, status, latency, environment, and version. Health checks log at debug level to avoid routine noise.

Request bodies, prompts, answers, PDF bytes/text, chunks, embeddings, keys, cookies, authorization headers, and database URLs are excluded from general HTTP logs. RAG query logging remains separately controlled, and question text is disabled by default.

## Implemented versus not implemented

Implemented:

- local Docker Compose release-like deployment
- migrations, health checks, readiness gates, persistent volumes
- provider-safe evidence fallback
- request IDs, structured logs, safe errors, security headers
- release verification, preflight, smoke testing, and operational docs

Not implemented:

- managed secrets, TLS termination, authentication, authorization, multi-tenancy
- cloud backups, object storage, autoscaling, Kubernetes, Helm, Terraform
- distributed workers, multi-replica coordination, managed monitoring
- Prometheus/Grafana, OpenTelemetry infrastructure, Sentry, formal on-call process

Those omissions are production requirements, not hidden assumptions.
