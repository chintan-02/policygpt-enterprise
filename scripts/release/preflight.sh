#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPOSITORY_ROOT}"

ENV_FILE="${COMPOSE_ENV_FILE:-.env.compose}"
[[ -f "${ENV_FILE}" ]] || {
  echo "FAIL: ${ENV_FILE} is missing. Copy .env.compose.example first." >&2
  exit 1
}

docker info >/dev/null
docker compose --env-file "${ENV_FILE}" config --quiet

read_env_value() {
  local key="$1"
  local fallback="$2"
  local value
  value="$(awk -v key="${key}" 'index($0, key "=") == 1 {sub(/^[^=]*=/, ""); print; exit}' "${ENV_FILE}")"
  printf '%s' "${value:-${fallback}}"
}

check_port() {
  local label="$1"
  local port="$2"
  if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "WARN: ${label} host port ${port} is already in use. Inspect it before startup."
  else
    echo "PASS: ${label} host port ${port} is available"
  fi
}

check_port PostgreSQL "$(read_env_value POSTGRES_HOST_PORT 5433)"
check_port backend "$(read_env_value BACKEND_HOST_PORT 8000)"
check_port frontend "$(read_env_value FRONTEND_HOST_PORT 3000)"

git check-ignore -q "${ENV_FILE}" || {
  echo "FAIL: ${ENV_FILE} is not ignored by Git." >&2
  exit 1
}

echo "PASS: release preflight completed without changing local state"
