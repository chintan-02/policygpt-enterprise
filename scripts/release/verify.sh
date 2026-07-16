#!/usr/bin/env bash

set -Eeuo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPOSITORY_ROOT}"

ENV_FILE="${COMPOSE_ENV_FILE:-.env.compose}"
SKIP_DOCKER_BUILD=false

usage() {
  echo "Usage: scripts/release/verify.sh [--skip-docker-build]"
}

for argument in "$@"; do
  case "${argument}" in
    --skip-docker-build) SKIP_DOCKER_BUILD=true ;;
    --help|-h) usage; exit 0 ;;
    *) echo "FAIL: unknown argument: ${argument}" >&2; usage >&2; exit 2 ;;
  esac
done

step() { echo; echo "==> $1"; }
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

if command -v rg >/dev/null 2>&1; then
  SEARCH_TOOL="rg"
elif command -v grep >/dev/null 2>&1; then
  SEARCH_TOOL="grep"
else
  fail "neither rg nor grep is available for required safety searches"
fi

recursive_pattern_search() {
  local pattern="$1"
  shift

  if [[ "${SEARCH_TOOL}" == "rg" ]]; then
    rg -n -e "${pattern}" "$@"
  else
    grep -E -R -n -- "${pattern}" "$@"
  fi
}

stream_pattern_search() {
  local pattern="$1"
  shift

  if [[ "${SEARCH_TOOL}" == "rg" ]]; then
    rg "$@" -e "${pattern}"
  else
    grep -E "$@" -- "${pattern}"
  fi
}

assert_no_recursive_match() {
  local pattern="$1"
  local failure_message="$2"
  local search_status
  shift 2

  if recursive_pattern_search "${pattern}" "$@" >/dev/null; then
    fail "${failure_message}"
  else
    search_status=$?
    if [[ ${search_status} -ne 1 ]]; then
      fail "required ${SEARCH_TOOL} safety search could not execute (status ${search_status})"
    fi
  fi
}

step "Required release files"
required_files=(
  README.md
  compose.yaml
  .env.compose.example
  docs/deployment-readiness.md
  docs/operations-runbook.md
  docs/portfolio-case-study.md
  docs/demo-guide.md
  scripts/compose/smoke-test.sh
  frontend/next.config.ts
  frontend/src/app/api/ready/route.ts
)
for file in "${required_files[@]}"; do
  [[ -f "${file}" ]] || fail "missing ${file}"
done
pass "required files exist"

step "Shell safety and syntax"
while IFS= read -r script; do
  bash -n "${script}"
done < <(find scripts -type f -name '*.sh' -print | sort)
forbidden_pattern="down"$' '"-v|docker"$' '"volume"$' '"rm|docker"$' '"system"$' '"prune|rm"$' '"-rf"$' '"data"
assert_no_recursive_match \
  "${forbidden_pattern}" \
  "a release or Compose script contains a destructive command" \
  scripts/release scripts/compose
pass "shell scripts are syntactically valid and non-destructive"

step "Repository hygiene"
git diff --check
if ! tracked_files="$(git ls-files)"; then
  fail "git could not enumerate tracked files"
fi
runtime_pattern='(^|/)(\.env|\.env\.local|\.env\.compose)$|^data/|^logs/|^frontend/(\.next|node_modules)/|^eval/results/'
if tracked_candidates="$(printf '%s\n' "${tracked_files}" | stream_pattern_search "${runtime_pattern}")"; then
  if tracked_runtime="$(printf '%s\n' "${tracked_candidates}" | stream_pattern_search '^(data|logs|eval/results)/\.gitkeep$' -v)"; then
    :
  else
    search_status=$?
    if [[ ${search_status} -eq 1 ]]; then
      tracked_runtime=""
    else
      fail "required ${SEARCH_TOOL} tracked-runtime exclusion search could not execute (status ${search_status})"
    fi
  fi
else
  search_status=$?
  if [[ ${search_status} -eq 1 ]]; then
    tracked_runtime=""
  else
    fail "required ${SEARCH_TOOL} tracked-runtime search could not execute (status ${search_status})"
  fi
fi
[[ -z "${tracked_runtime}" ]] || fail "tracked runtime files detected: ${tracked_runtime}"
if ! staged_diff="$(git diff --cached --unified=0)"; then
  fail "git could not inspect staged changes"
fi
if ! staged_additions="$(printf '%s\n' "${staged_diff}" | sed -n 's/^+//p')"; then
  fail "staged additions could not be extracted for secret scanning"
fi
secret_pattern='(groq_api_key|openai_api_key)=[[:space:]]*[^[:space:]$]+|postgresql\+psycopg://[^:[:space:]]+:[^@[:space:]]+@'
if secret_candidates="$(printf '%s\n' "${staged_additions}" | stream_pattern_search "${secret_pattern}" -i)"; then
  if printf '%s\n' "${secret_candidates}" | stream_pattern_search 'your_|example|placeholder|change_me' -i -v >/dev/null; then
    fail "a staged change appears to contain a secret"
  else
    search_status=$?
    if [[ ${search_status} -ne 1 ]]; then
      fail "required ${SEARCH_TOOL} staged-secret exclusion search could not execute (status ${search_status})"
    fi
  fi
else
  search_status=$?
  if [[ ${search_status} -ne 1 ]]; then
    fail "required ${SEARCH_TOOL} staged-secret search could not execute (status ${search_status})"
  fi
fi
pass "diff and tracked-runtime checks passed"

step "Backend test suite"
[[ -x .venv/bin/python ]] || fail ".venv is missing; create the documented virtual environment"
.venv/bin/python -m pytest -q tests
pass "backend tests passed"

step "Evaluation dataset"
.venv/bin/python eval/validate_dataset.py
pass "evaluation dataset validation passed"

step "Frontend validation"
(
  cd frontend
  npm run lint
  npm run test
  npm run build
)
pass "frontend lint, tests, and production build passed"

step "Compose configuration"
[[ -f "${ENV_FILE}" ]] || fail "${ENV_FILE} is missing; copy .env.compose.example and configure it"
compose=(docker compose --env-file "${ENV_FILE}")
"${compose[@]}" config --quiet
services="$("${compose[@]}" config --services | sort)"
expected_services=$'backend\nfrontend\nmigrate\npostgres'
[[ "${services}" == "${expected_services}" ]] || fail "unexpected Compose services: ${services}"
pass "Compose configuration and service set are valid"

if [[ "${SKIP_DOCKER_BUILD}" == false ]]; then
  step "Release image build"
  "${compose[@]}" build
  pass "backend and frontend images built"
else
  echo
  echo "SKIP: Docker image build; run it before release."
fi

echo
echo "PASS: release verification completed"
echo "Manual runtime gate: start Compose and run scripts/compose/smoke-test.sh."
