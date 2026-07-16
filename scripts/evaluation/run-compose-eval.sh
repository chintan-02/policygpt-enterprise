#!/usr/bin/env bash

set -Eeuo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPOSITORY_ROOT}"

ENV_FILE="${COMPOSE_ENV_FILE:-.env.compose}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "FAIL: ${ENV_FILE} does not exist. Copy .env.compose.example first." >&2
  exit 1
fi

if [[ $# -gt 1 ]]; then
  echo "Usage: bash scripts/evaluation/run-compose-eval.sh [request-delay-seconds]" >&2
  exit 2
fi

request_delay="${1:-0}"
if [[ ! "${request_delay}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "FAIL: request delay must be a finite non-negative number." >&2
  exit 2
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

backend_port="$(read_env_value BACKEND_HOST_PORT 8000)"
if [[ ! "${backend_port}" =~ ^[0-9]+$ ]] || (( backend_port < 1 || backend_port > 65535 )); then
  echo "FAIL: BACKEND_HOST_PORT must be an integer from 1 to 65535." >&2
  exit 1
fi

python_bin="${REPOSITORY_ROOT}/.venv/bin/python"
if [[ ! -x "${python_bin}" ]]; then
  echo "FAIL: ${python_bin} is unavailable. Create the project virtual environment first." >&2
  exit 1
fi

compose=(docker compose --env-file "${ENV_FILE}")
if ! "${compose[@]}" ps --status running --services | grep -qx backend; then
  echo "FAIL: the Compose backend service is not running." >&2
  exit 1
fi

backend_base="http://127.0.0.1:${backend_port}"
if ! curl --fail --silent --show-error --output /dev/null "${backend_base}/api/v1/health"; then
  echo "FAIL: the backend is unavailable at ${backend_base}." >&2
  exit 1
fi

"${python_bin}" eval/run_eval.py \
  --base-url "${backend_base}" \
  --dataset eval/questions.jsonl \
  --output-dir eval/results \
  --request-delay-seconds "${request_delay}"

json_path="eval/results/latest_eval_results.json"
csv_path="eval/results/latest_eval_results.csv"
if [[ ! -s "${json_path}" || ! -s "${csv_path}" ]]; then
  echo "FAIL: the evaluation runner did not produce both JSON and CSV artifacts." >&2
  exit 1
fi

temporary_suffix="compose-eval-$$"
json_temporary="/app/eval/results/.latest_eval_results.json.${temporary_suffix}"
csv_temporary="/app/eval/results/.latest_eval_results.csv.${temporary_suffix}"

"${compose[@]}" cp "${json_path}" "backend:${json_temporary}"
"${compose[@]}" cp "${csv_path}" "backend:${csv_temporary}"
"${compose[@]}" exec -T -u 0 backend sh -eu -c '
  chown 10001:10001 "$1" "$2"
  chmod 0644 "$1" "$2"
  mv -f "$1" /app/eval/results/latest_eval_results.json
  mv -f "$2" /app/eval/results/latest_eval_results.csv
' sh "${json_temporary}" "${csv_temporary}"

status_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${backend_base}/api/v1/evaluations/latest")"
if [[ "${status_code}" != "200" ]]; then
  echo "FAIL: backend evaluation verification returned HTTP ${status_code}." >&2
  exit 1
fi

echo "PASS: 16-case evaluation artifacts were generated and atomically copied."
echo "PASS: backend evaluation API returned HTTP 200."
