# Docker Compose local deployment

The root `compose.yaml` runs the complete local PolicyGPT stack with four
services on a private bridge network:

| Service | Purpose | Host exposure |
| --- | --- | --- |
| `postgres` | PostgreSQL 16 document metadata | `127.0.0.1:${POSTGRES_HOST_PORT}` |
| `migrate` | One-shot `alembic upgrade head` gate | none |
| `backend` | FastAPI, ChromaDB, uploads, logs, and evaluation reads | `127.0.0.1:${BACKEND_HOST_PORT}` |
| `frontend` | Production Next.js standalone server | `127.0.0.1:${FRONTEND_HOST_PORT}` |

The startup dependency chain is intentional: PostgreSQL must be healthy,
the migration must exit successfully, FastAPI must be healthy, and only then
does the frontend start. The migration service is not a long-running process.

This is a reproducible local deployment profile, not a cloud-production
deployment. Authentication, TLS termination, external object storage, managed
PostgreSQL, background workers, and multi-replica coordination remain outside
this step.

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- At least 8 GB of memory available to Docker for the first image build
- Internet access during the first build to download Python, Node, package, and
  SentenceTransformer model artifacts
- Free local ports `3000`, `8000`, and `5433`, or alternate values in the env
  file

Both application images run as non-root users. No Docker socket, privileged
mode, host networking, or host filesystem bind mount is used. The backend image
caches the configured embedding model at build time so normal startup does not
download it again. Apple silicon and x86_64 use Docker's native architecture;
the Compose file does not force an emulated platform.

`EMBEDDING_MODEL_REVISION` pins the public model snapshot used by the image.
If `EMBEDDING_MODEL_NAME` is intentionally changed, its matching immutable
revision and the model-file list in the backend Dockerfile must be reviewed
together; otherwise the build fails instead of silently caching different
weights.

Before starting, check for native services or an older container already using
the default ports. These commands are read-only; stop conflicts deliberately
rather than killing processes automatically:

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5433 -sTCP:LISTEN
docker ps
```

## Configure the stack

From the repository root:

```bash
cp .env.compose.example .env.compose
```

Edit `.env.compose` before starting. At minimum, replace the example PostgreSQL
password. Keep secrets only in `.env.compose`; it is ignored by Git. Do not use
reserved URL characters in the local database password unless they are
percent-encoded for a database URL.

Provider credentials are optional. With `LLM_PROVIDER=none` and empty provider
keys, retrieval and citations remain available and answer generation uses the
existing safe citation-only fallback. The browser-facing frontend receives
only explicitly named `NEXT_PUBLIC_*` values. `FASTAPI_URL` stays server-only
and resolves to `http://backend:8000` inside the Compose network.

Validate the resolved configuration without starting containers:

```bash
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose config --services
```

## Build and start

```bash
docker compose --env-file .env.compose build
docker compose --env-file .env.compose up -d
docker compose --env-file .env.compose ps -a
```

The first backend build downloads and caches the embedding model and can take
several minutes. A normal successful `ps -a` result shows `postgres`, `backend`,
and `frontend` running and healthy; `migrate` should be exited with code `0`.

Open:

- Product UI: <http://localhost:3000>
- FastAPI documentation: <http://localhost:8000/docs>
- FastAPI health: <http://localhost:8000/api/v1/health>
- Frontend health proxy: <http://localhost:3000/api/health>

If alternate host ports were configured, use those ports instead. Service-to-
service URLs do not change because containers use internal ports and DNS names.

## Operate and inspect

```bash
# Follow all service output
docker compose --env-file .env.compose logs -f

# Focused and bounded log reads
docker compose --env-file .env.compose logs -f backend
docker compose --env-file .env.compose logs -f frontend
docker compose --env-file .env.compose logs -f postgres
docker compose --env-file .env.compose logs migrate
docker compose --env-file .env.compose logs --tail=100

# Restart an application service
docker compose --env-file .env.compose restart backend
docker compose --env-file .env.compose restart frontend

# Stop containers while preserving every named volume
docker compose --env-file .env.compose down

# Start the same persisted stack again
docker compose --env-file .env.compose up -d

# Rebuild and replace one service
docker compose --env-file .env.compose build backend
docker compose --env-file .env.compose up -d backend
```

Container output uses Docker's bounded `json-file` logging configuration.
Structured backend output remains on stdout/stderr. The dedicated logs volume
stores the existing RAG query log when that feature is enabled; it is not a
replacement for container logs.

## Health and smoke tests

Run the read-only smoke test after startup:

```bash
scripts/compose/smoke-test.sh
```

Use `COMPOSE_ENV_FILE` if the env file has another name:

```bash
COMPOSE_ENV_FILE=.env.compose.validation scripts/compose/smoke-test.sh
```

The script confirms container health, the migration exit code, FastAPI health,
the frontend health route, and the document-list path. It does not upload a
file, invoke an LLM provider, or modify stored data.

For direct inspection:

```bash
docker compose --env-file .env.compose exec -T backend id
docker compose --env-file .env.compose exec -T frontend id
docker compose --env-file .env.compose exec -T backend python -c \
  'from app.services.embedding_service import EmbeddingService; service = EmbeddingService(); print(service.model.get_sentence_embedding_dimension())'
```

The first two commands should report non-root identities. The last command
forces the configured embedding model to load from the image cache and prints
its embedding dimension without downloading a second model.

The release backend image intentionally excludes test sources. Run backend tests
through the native virtualenv as described in the root README so test fixtures
do not enter the production build context.

## Optional sample ingestion

A fresh stack has no indexed documents. Sample ingestion is explicit and is
never part of startup or migrations:

```bash
curl -X POST \
  http://localhost:8000/api/v1/documents/upload \
  -H 'accept: application/json' \
  -F 'file=@examples/sample_hr_policy.pdf'
```

Record the returned UUID for persistence checks. Repeating this upload is safe:
the existing SHA-256 duplicate behavior returns the same document record and
does not create a second vector index.

## Persistent data

The stack uses five named volumes. Their default names are deliberately stable:

| Environment setting | Default volume | Data |
| --- | --- | --- |
| `POSTGRES_VOLUME_NAME` | `policygpt_postgres_data` | PostgreSQL cluster |
| `CHROMA_VOLUME_NAME` | `policygpt_chroma_data` | Embedded Chroma vectors |
| `UPLOADS_VOLUME_NAME` | `policygpt_uploads_data` | Source PDFs |
| `LOGS_VOLUME_NAME` | `policygpt_logs_data` | Optional RAG query log |
| `EVALUATION_RESULTS_VOLUME_NAME` | `policygpt_evaluation_results_data` | Evaluation artifacts |

`docker compose down` preserves these volumes. Rebuilding images also preserves
them. A normal restart therefore retains PostgreSQL metadata, Chroma vectors,
uploaded PDFs, logs, and evaluation artifacts.

To verify persistence without changing product data:

```bash
docker compose --env-file .env.compose down
docker compose --env-file .env.compose up -d
scripts/compose/smoke-test.sh
```

For a stronger manual check, upload `examples/sample_hr_policy.pdf`, record its
document UUID, perform the stop/start sequence above, and confirm both the same
document detail route and Ask evidence still work. Re-uploading the same PDF
should return the existing duplicate record rather than create a second index.

## Fresh start versus importing native data

A fresh Compose start intentionally creates empty named volumes. It does not
silently copy the repository's `data/chroma`, `data/uploads`, `logs`, or
`eval/results` directories. This avoids combining vector data, metadata, and
files that may not belong to the same ingestion history.

If those host directories form a known-consistent native dataset, import them
only into empty Compose volumes while the stack is stopped:

```bash
docker compose --env-file .env.compose down
COMPOSE_ENV_FILE=.env.compose scripts/compose/import-local-data.sh
docker compose --env-file .env.compose up -d
scripts/compose/smoke-test.sh
```

The import script is intentionally conservative: it refuses to run while a
Compose service is running, refuses non-empty target volumes, never modifies
the source directories, excludes environment files, and never imports
PostgreSQL. It prints every planned mapping before copying. Database metadata
must already correspond to the imported files and vectors; otherwise use a
fresh stack and ingest the PDFs through the application.

## Reusing an existing standalone PostgreSQL volume

An older native workflow may already run a standalone container such as
`policygpt-postgres`. Never create a second PostgreSQL container against the
same volume, and never remove the old volume during migration.

First inspect the existing container and record the exact named volume:

```bash
docker inspect policygpt-postgres \
  --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}'
```

Confirm that the PostgreSQL mount targets `/var/lib/postgresql/data`. Then stop
and remove only the old container, preserving its named volume:

```bash
docker stop policygpt-postgres
docker rm policygpt-postgres
```

Set the recorded name in `.env.compose`, for example:

```dotenv
POSTGRES_VOLUME_NAME=the_existing_named_volume
```

Start Compose and inspect the migration before using the application:

```bash
docker compose --env-file .env.compose up -d
docker compose --env-file .env.compose logs migrate
docker compose --env-file .env.compose ps -a
```

This reuses the PostgreSQL data only. Chroma vectors and source PDFs must also
be kept consistent with those metadata rows. If that relationship is uncertain,
stop and make a backup before proceeding.

## Failure and recovery checks

The following checks are safe for a disposable or backed-up local stack.

PostgreSQL outage:

```bash
docker compose --env-file .env.compose stop postgres
curl -i http://localhost:8000/api/v1/documents
docker compose --env-file .env.compose start postgres
docker compose --env-file .env.compose restart backend
```

The document endpoint should report an unavailable service while PostgreSQL is
stopped. After PostgreSQL is healthy and FastAPI is restarted, the registry
should recover without data loss.

Backend outage:

```bash
docker compose --env-file .env.compose stop backend
curl -i http://localhost:3000/api/health
docker compose --env-file .env.compose start backend
```

The frontend health proxy should return its controlled unavailable response,
not expose the internal service URL. The frontend container itself stays up.

Migration failure gate, using a deliberately unreachable database host:

```bash
docker compose --env-file .env.compose run --rm --no-deps \
  -e 'DATABASE_URL=postgresql+psycopg://policygpt:invalid@invalid-host:5432/policygpt' \
  migrate
```

The command must exit non-zero. In normal startup, that failed completion
prevents the dependent backend and frontend from starting.

## DESTRUCTIVE LOCAL RESET

> **Warning:** The following command permanently deletes all Compose-managed
> PostgreSQL metadata, Chroma vectors, uploaded PDFs, logs, and evaluation
> artifacts. It cannot be undone. Run it only when a complete local reset is
> explicitly intended and after making any required backups.

```bash
docker compose --env-file .env.compose down -v
```

Do not use `docker volume prune` as a reset procedure. It has a broader scope
than this repository.

## Troubleshooting

- `port is already allocated`: stop the native service using the port or change
  `POSTGRES_HOST_PORT`, `BACKEND_HOST_PORT`, or `FRONTEND_HOST_PORT`.
- `migrate` exits non-zero: inspect `docker compose ... logs postgres migrate`;
  do not bypass the migration gate.
- backend build cannot download the model: restore build-time network access and
  rebuild; runtime startup is intentionally offline-capable for that model.
- backend is unhealthy: inspect its logs and confirm all named volumes are
  writable by the image's non-root user.
- provider fallback is shown: configure the selected provider key, or keep
  `LLM_PROVIDER=none` for the expected safe citation-only behavior.
- native development is still supported: use `.env` plus the virtualenv and
  `.env.local` plus `npm run dev`; do not run native and Compose services on the
  same host ports at the same time.
