# Document metadata database

PostgreSQL is the source of truth for document identity, ingestion lifecycle,
safe file metadata, counts, and indexing timestamps. ChromaDB remains the source
of truth for chunk text, embeddings, and vector retrieval. Source PDFs are stored
under `DOCUMENT_STORAGE_DIR` using generated keys such as
`documents/<uuid>/source.pdf`; database and API records never expose an absolute
filesystem path.

The documents table intentionally does not store PDF bytes, extracted text,
chunks, embeddings, prompts, or evidence excerpts.

## Local configuration and startup

For native development, set a non-placeholder `DATABASE_URL` in `.env`. If the
standalone development container is named `policygpt-postgres`, start it before
running migrations:

```bash
docker start policygpt-postgres

source .venv/bin/activate
alembic upgrade head

python -m uvicorn app.api.main:app \
  --reload \
  --reload-dir app \
  --host 0.0.0.0 \
  --port 8000
```

Useful migration checks:

```bash
alembic current
alembic downgrade -1
alembic upgrade head
```

FastAPI never creates tables automatically; Alembic is the production schema
source of truth.

For the complete local deployment, use the repository-root Compose stack. Its
one-shot `migrate` service applies Alembic only after PostgreSQL is healthy and
must succeed before FastAPI starts. The stack's database URL is internal and
uses the `postgres` service name rather than `localhost`. See
[Docker Compose local deployment](docker-compose.md), including the safe process
for reusing an existing standalone PostgreSQL named volume without deleting it.

## Lifecycle and duplicate behavior

A new upload moves through `received`, `stored`, `extracting`, `cleaning`,
`chunking`, `embedding`, `indexing`, and `complete`. Its status is `processing`
until Chroma indexing and the final metadata update both succeed, then becomes
`ready`. A safe error code and message are retained with `failed / failed` when
ingestion cannot complete.

The complete source file is SHA-256 hashed before ingestion. A matching ready,
processing, or failed row is returned with `duplicate=true`; it is not indexed
again and a second metadata row is not created.

Read-only contracts:

- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/status`

The Next.js Documents product consumes these contracts for the registry, detail,
lifecycle, filtering, pagination, upload, duplicate, and outage states. Delete,
reindex, source download, and document-scoped Ask remain intentionally unavailable.

## Database readiness

`GET /api/v1/ready` executes a lightweight `SELECT 1` through the existing
SQLAlchemy engine and closes the connection. Failure maps to a sanitized
`database: unavailable` state and HTTP 503. The response and logs never include
the connection URL, credentials, host, port, driver exception text, or stack
trace.

Database readiness is required for deployment health. Process liveness at
`GET /api/v1/health` remains independent and returns 200 while PostgreSQL is
offline, which lets operators distinguish a running API from a ready service.

The connection pool uses pre-ping and bounded pool acquisition. Readiness does
not create tables; Alembic remains the only schema authority.

## Backup and recovery ownership

PostgreSQL metadata must be backed up consistently with the Chroma volume and
uploaded source files. A document row without its source or vectors is not a
complete ingestion record. Named volumes preserve restarts but are not backups.
See [deployment readiness](deployment-readiness.md) and the
[operations runbook](operations-runbook.md) for recovery guidance.

## Resetting pre-PostgreSQL development vectors

Existing Chroma vectors cannot be safely reverse-migrated into complete document
metadata. For development only:

1. Stop FastAPI.
2. Remove the local Chroma development directory.
3. Run `alembic upgrade head`.
4. Restart FastAPI.
5. Upload `examples/sample_hr_policy.pdf` once.

This reset is never performed automatically. Production data must not be deleted
from application startup.
