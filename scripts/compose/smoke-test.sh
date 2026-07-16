#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPOSITORY_ROOT}"

ENV_FILE="${COMPOSE_ENV_FILE:-.env.compose}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "FAIL: ${ENV_FILE} does not exist. Copy .env.compose.example first." >&2
  exit 1
fi

compose=(docker compose --env-file "${ENV_FILE}")

read_env_value() {
  local key="$1"
  local fallback="$2"
  local value
  value="$(awk -v key="${key}" '
    index($0, key "=") == 1 {
      sub(/^[^=]*=/, "")
      gsub(/\r$/, "")
      print
      exit
    }
  ' "${ENV_FILE}")"
  printf '%s' "${value:-${fallback}}"
}

require_running_service() {
  local service="$1"
  if ! "${compose[@]}" ps --status running --services | grep -qx "${service}"; then
    echo "FAIL: Compose service ${service} is not running." >&2
    exit 1
  fi
  echo "PASS: ${service} is running"
}

require_healthy_service() {
  local service="$1"
  local container_id
  local health
  container_id="$("${compose[@]}" ps -q "${service}")"
  if [[ -z "${container_id}" ]]; then
    echo "FAIL: Compose service ${service} has no container." >&2
    exit 1
  fi
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${container_id}")"
  if [[ "${health}" != "healthy" ]]; then
    echo "FAIL: ${service} health is ${health}." >&2
    exit 1
  fi
  echo "PASS: ${service} is healthy"
}

require_migration_success() {
  local container_id
  local state
  container_id="$("${compose[@]}" ps -a -q migrate)"
  if [[ -z "${container_id}" ]]; then
    echo "FAIL: migrate has no completed container." >&2
    exit 1
  fi
  state="$(docker inspect --format '{{.State.Status}} {{.State.ExitCode}}' "${container_id}")"
  if [[ "${state}" != "exited 0" ]]; then
    echo "FAIL: migrate state is ${state}." >&2
    exit 1
  fi
  echo "PASS: migrate exited successfully"
}

wait_for_http() {
  local label="$1"
  local url="$2"
  local attempt
  for attempt in $(seq 1 60); do
    if curl --fail --silent --show-error --output /dev/null "${url}" 2>/dev/null; then
      echo "PASS: ${label} is reachable"
      return 0
    fi
    sleep 2
  done
  echo "FAIL: ${label} did not become reachable: ${url}" >&2
  return 1
}

require_json_response() {
  local label="$1"
  local url="$2"
  local body
  body="$(curl --fail --silent --show-error "${url}")"
  if ! printf '%s' "${body}" | "${compose[@]}" exec -T backend \
    python -c 'import json, sys; json.load(sys.stdin)' >/dev/null; then
    echo "FAIL: ${label} did not return valid JSON." >&2
    exit 1
  fi
  echo "PASS: ${label} returned JSON"
}

backend_port="$(read_env_value BACKEND_HOST_PORT 8000)"
frontend_port="$(read_env_value FRONTEND_HOST_PORT 3000)"
backend_base="http://127.0.0.1:${backend_port}"
frontend_base="http://127.0.0.1:${frontend_port}"

require_running_service postgres
require_running_service backend
require_running_service frontend
require_migration_success
require_healthy_service postgres
require_healthy_service backend
require_healthy_service frontend

wait_for_http "backend health" "${backend_base}/api/v1/health"
wait_for_http "frontend health" "${frontend_base}/api/health"
wait_for_http "Documents page" "${frontend_base}/documents"

require_json_response "backend health" "${backend_base}/api/v1/health"
require_json_response "frontend health" "${frontend_base}/api/health"
require_json_response "Documents list BFF" "${frontend_base}/api/documents?limit=1&offset=0"

echo "PASS: PolicyGPT Compose smoke test completed"
