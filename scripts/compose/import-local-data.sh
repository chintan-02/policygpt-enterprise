#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPOSITORY_ROOT}"

ENV_FILE="${COMPOSE_ENV_FILE:-.env.compose}"
UTILITY_IMAGE="alpine:3.20"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} does not exist. Copy .env.compose.example first." >&2
  exit 1
fi

compose=(docker compose --env-file "${ENV_FILE}")

running_services="$("${compose[@]}" ps --status running --services 2>/dev/null || true)"
if [[ -n "${running_services}" ]]; then
  echo "ERROR: Compose services must be stopped before importing local data." >&2
  printf '%s\n' "${running_services}" >&2
  exit 1
fi

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

volume_is_empty() {
  local volume="$1"
  docker run --rm --volume "${volume}:/target" "${UTILITY_IMAGE}" \
    sh -eu -c 'test -z "$(find /target -mindepth 1 -maxdepth 1 -print -quit)"'
}

source_has_data() {
  local source="$1"
  [[ -d "${source}" ]] && [[ -n "$(find "${source}" -mindepth 1 -maxdepth 1 -print -quit)" ]]
}

validate_pair() {
  local source="$1"
  local volume="$2"

  if ! source_has_data "${source}"; then
    echo "SKIP: ${source} is missing or empty"
    return 0
  fi

  if [[ -n "$(find "${source}" -type f -name '.env*' -print -quit)" ]]; then
    echo "ERROR: ${source} contains an environment file; refusing to copy it." >&2
    exit 1
  fi

  if [[ ! "${volume}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]]; then
    echo "ERROR: Invalid Docker volume name: ${volume}" >&2
    exit 1
  fi

  docker volume inspect "${volume}" >/dev/null 2>&1 || docker volume create "${volume}" >/dev/null
  if ! volume_is_empty "${volume}"; then
    echo "ERROR: target volume ${volume} is not empty; nothing was overwritten." >&2
    exit 1
  fi

  echo "PLAN: copy ${source} -> Docker volume ${volume}"
}

copy_pair() {
  local source="$1"
  local volume="$2"
  local source_absolute

  if ! source_has_data "${source}"; then
    return 0
  fi

  source_absolute="$(cd "${source}" && pwd -P)"
  docker run --rm \
    --volume "${source_absolute}:/source:ro" \
    --volume "${volume}:/target" \
    "${UTILITY_IMAGE}" \
    sh -eu -c 'cd /source; tar --exclude=".env" --exclude=".env.*" -cf - . | tar -xf - -C /target; chown -R 10001:10001 /target'
  echo "COPIED: ${source} -> ${volume}"
}

chroma_volume="$(read_env_value CHROMA_VOLUME_NAME policygpt_chroma_data)"
uploads_volume="$(read_env_value UPLOADS_VOLUME_NAME policygpt_uploads_data)"
logs_volume="$(read_env_value LOGS_VOLUME_NAME policygpt_logs_data)"
evaluation_volume="$(read_env_value EVALUATION_RESULTS_VOLUME_NAME policygpt_evaluation_results_data)"

echo "Optional one-time import; source directories are read-only and are never deleted."

# Preflight every target before copying anything so an occupied volume cannot
# cause a partially completed import.
validate_pair data/chroma "${chroma_volume}"
validate_pair data/uploads "${uploads_volume}"
validate_pair logs "${logs_volume}"
validate_pair eval/results "${evaluation_volume}"

copy_pair data/chroma "${chroma_volume}"
copy_pair data/uploads "${uploads_volume}"
copy_pair logs "${logs_volume}"
copy_pair eval/results "${evaluation_volume}"

echo "Import complete. Host source directories were preserved."
