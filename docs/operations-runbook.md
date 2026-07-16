# Operations runbook

This runbook assumes repository-root commands and an ignored `.env.compose`. Substitute actual configured host ports; the scripts read them automatically.

## Start and verify

```bash
scripts/release/preflight.sh
docker compose --env-file .env.compose up -d
docker compose --env-file .env.compose ps -a
docker compose --env-file .env.compose logs migrate
scripts/compose/smoke-test.sh
```

Expected state: PostgreSQL, backend, and frontend are healthy; `migrate` is `exited (0)`.

## Stop safely

> `docker compose --env-file .env.compose down` preserves PostgreSQL, Chroma, uploaded PDFs, logs, and evaluation artifacts in named volumes.

```bash
docker compose --env-file .env.compose down
```

> **Destructive warning:** `docker compose --env-file .env.compose down -v` permanently deletes Compose-managed volumes and their data. Do not use it for routine stop, restart, rollback, or troubleshooting.

## Restart

```bash
docker compose --env-file .env.compose restart backend frontend
docker compose --env-file .env.compose ps -a
scripts/compose/smoke-test.sh
```

For a full preserved stop/start, run safe `down`, then `up -d`.

## Inspect services and logs

```bash
docker compose --env-file .env.compose ps -a
docker compose --env-file .env.compose logs --tail=100
docker compose --env-file .env.compose logs --tail=100 backend
docker compose --env-file .env.compose logs --tail=100 frontend
docker compose --env-file .env.compose logs migrate
docker compose --env-file .env.compose logs --tail=100 postgres
```

Use the response `X-Request-ID` to correlate a request with backend structured logs. Do not paste secrets or full user prompts into incident notes.

## Direct operational checks

Read actual ports from `.env.compose`, then:

```bash
curl -i http://127.0.0.1:<BACKEND_HOST_PORT>/api/v1/health
curl -i http://127.0.0.1:<BACKEND_HOST_PORT>/api/v1/ready
curl -i http://127.0.0.1:<FRONTEND_HOST_PORT>/api/health
curl -i http://127.0.0.1:<FRONTEND_HOST_PORT>/api/ready
```

Liveness must remain 200 during dependency outages. Readiness must return 503 when PostgreSQL or Chroma is inaccessible.

## Verify migrations

```bash
docker compose --env-file .env.compose logs migrate
docker compose --env-file .env.compose exec -T backend alembic current
docker compose --env-file .env.compose exec -T backend alembic heads
```

Do not run a downgrade without a reviewed rollback plan and backup.

## Verify document metadata

```bash
docker compose --env-file .env.compose exec -T postgres \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "select id, filename, status, processing_stage, chunk_count, indexed_at from documents order by created_at desc limit 10;"'
```

The database name and user expand inside the container. Never put the password in command history.

## Verify Chroma-backed retrieval

Use an indexed document and a supported question:

```bash
curl -sS http://127.0.0.1:<BACKEND_HOST_PORT>/api/v1/documents/evidence \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is the remote work policy?","top_k":5}'
```

Confirm real citations, page numbers, and `answer_ready`; do not treat an empty fresh store as a service outage.

## Verify a source file

From a known document record, inspect the generated storage key inside the backend container without returning it through the API:

```bash
docker compose --env-file .env.compose exec -T backend \
  find /app/data/uploads/documents -type f -name source.pdf -maxdepth 3 -print
```

Restrict this operator-only command because source PDFs may contain sensitive material.

## Diagnose PostgreSQL unavailable

1. Confirm backend liveness and readiness responses.
2. Inspect `postgres` health and logs.
3. Confirm the migration state and database environment were not changed.
4. Check disk space and volume attachment.
5. Start or restore PostgreSQL; do not delete its volume.
6. Re-run readiness and the Documents list.

## Diagnose backend unavailable

1. Inspect backend state and the last 100 log lines.
2. Confirm migration exited 0 and PostgreSQL is healthy.
3. Validate `.env.compose` with `docker compose ... config --quiet` without printing the resolved config into shared logs.
4. Check Chroma and uploads volume permissions.
5. Restart backend and verify liveness before readiness.

## Diagnose frontend unavailable

1. Check the frontend container and logs.
2. Verify backend readiness separately.
3. Confirm `FASTAPI_URL` exists only in the server container environment.
4. Restart frontend and check `/api/ready`, then `/documents`.

## Diagnose provider unavailable

Provider failure does not make deployment readiness fail. Confirm evidence retrieval works and Ask returns citation-only fallback with evidence cards. Check only whether the selected provider and key are intentionally configured; never print the key. Provider reachability is not probed by the System page.

## Refresh the Compose evaluation artifact

Evaluation pages are read-only. Start a benchmark explicitly from the
repository root:

```bash
bash scripts/evaluation/run-compose-eval.sh
```

The helper reads `BACKEND_HOST_PORT` from `.env.compose`, runs all 16 cases,
verifies the JSON and CSV outputs, and atomically replaces the two artifact
files inside the running backend's existing evaluation-results volume. Pass an
optional request delay as the first argument, for example
`bash scripts/evaluation/run-compose-eval.sh 5`. The helper does not recreate
volumes or start evaluation work from the browser.

## Recover from a port conflict

```bash
lsof -nP -iTCP:<PORT> -sTCP:LISTEN
docker ps
```

Identify the owner. Stop it deliberately or choose an alternate `POSTGRES_HOST_PORT`, `BACKEND_HOST_PORT`, or `FRONTEND_HOST_PORT` in `.env.compose`. Do not kill processes automatically. Internal container ports and service URLs remain unchanged.

## Backup guidance

Back up PostgreSQL with a database-consistent tool and coordinate snapshots of Chroma and uploads. Preserve volume names and the application version. Test restoration into isolated volumes before relying on it. Logs and evaluation artifacts may have separate retention policies.

Named volumes are not backups. A source PDF, its PostgreSQL row, and its Chroma chunks should be restored as one logical ingestion record.
