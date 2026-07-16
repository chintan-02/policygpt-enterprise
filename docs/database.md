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

Step 15A will consume these contracts. Delete, reindex, download, document-scoped
Ask, and document-management UI are intentionally not part of Step 15.

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
