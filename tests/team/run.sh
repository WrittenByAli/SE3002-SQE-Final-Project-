#!/usr/bin/env bash
# One entry point for every team test target. Same commands run locally and in CI.
#
#   bash tests/team/run.sh env-up        start the Indico app stack (http://localhost:8081)
#   bash tests/team/run.sh env-reset     wipe + reseed the app (writes tests/team/.env.test)
#   bash tests/team/run.sh unit          tests/team/unit + coverage reports      (Linux container: Py3.12 + Postgres)
#   bash tests/team/run.sh mutation ...  mutmut, args passed through (default: run) (Linux container)
#   bash tests/team/run.sh api           tests/team/api against the running app  (host Python)
#   bash tests/team/run.sh e2e           tests/team/e2e Playwright (Chromium) against the running app (Node)
#   bash tests/team/run.sh perf <x.js>   k6 script from tests/team/perf/          (Docker grafana/k6)
#   bash tests/team/run.sh harness       static checks of the harness itself (fast, no Docker)
#   bash tests/team/run.sh shell         interactive shell in the Linux test runner
#
# Reports land in tests/team/reports/<target>/ (gitignored; CI uploads them as artifacts).
set -euo pipefail
export MSYS_NO_PATHCONV=1

# Git Bash on Windows: hand Windows tools (python, docker) "D:/x" paths, not "/d/x". No-op on Linux/macOS/CI.
native() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }
ROOT="$(native "$(cd "$(dirname "$0")/../.." && pwd)")"
REPORTS="$ROOT/tests/team/reports"
RUNNER=(docker compose -f "$ROOT/infra/test-runner/docker-compose.yml")
APP_DIR="$ROOT/infra/indico-containers/indico-prod"
PY="${PYTHON:-python}"
target="${1:-help}"; shift || true

in_runner() {   # run a command inside the Linux test runner (inside CI we are already on Linux with deps)
  if [[ "${SQE_IN_RUNNER:-0}" == "1" ]]; then bash -c "$*"; else
    "${RUNNER[@]}" run --rm -e SQE_IN_RUNNER=1 runner bash -c "$*"; fi
}

case "$target" in
  env-up)
    (cd "$APP_DIR" && [[ -f .env ]] || { echo "Create $APP_DIR/.env from .env.example first"; exit 1; })
    (cd "$APP_DIR" && docker compose up -d --build) ;;
  env-reset)
    bash "$ROOT/tests/team/seed/reset.sh" ;;
  unit)
    mkdir -p "$REPORTS/unit"
    in_runner "pytest tests/team/unit -p no:cacheprovider --cov=indico/modules/rb --cov-branch \
      --cov-report=json:tests/team/reports/unit/coverage.json --cov-report=html:tests/team/reports/unit/htmlcov \
      --cov-report=xml:tests/team/reports/unit/coverage.xml \
      --junitxml=tests/team/reports/unit/junit.xml -q $*" ;;
  mutation)
    mkdir -p "$REPORTS/mutation"
    in_runner "mutmut ${*:-run}" ;;
  api)
    mkdir -p "$REPORTS/api"
    [[ -f "$ROOT/tests/team/.env.test" ]] || { echo "Run: bash tests/team/run.sh env-reset"; exit 1; }
    "$PY" -m pytest -c "$ROOT/tests/team/api/pytest.ini" "$ROOT/tests/team/api" \
      --junitxml="$REPORTS/api/junit.xml" "$@" ;;
  e2e)
    [[ -f "$ROOT/tests/team/.env.test" ]] || { echo "Run: bash tests/team/run.sh env-reset"; exit 1; }
    (cd "$ROOT/tests/team/e2e" && { [[ -d node_modules ]] || npm ci; } && npx playwright test "$@") ;;
  perf)
    mkdir -p "$REPORTS/perf"
    [[ -f "$ROOT/tests/team/.env.test" ]] || { echo "Run: bash tests/team/run.sh env-reset"; exit 1; }
    [[ -n "${1:-}" ]] || { echo "Usage: bash tests/team/run.sh perf <script.js in tests/team/perf/>"; exit 1; }
    docker run --rm --env-file "$ROOT/tests/team/.env.test" -e K6_BASE_URL=http://host.docker.internal:8081 \
      -v "$ROOT/tests/team/perf:/scripts" -v "$REPORTS/perf:/out" grafana/k6:1.3.0 run "/scripts/$1" ;;
  harness)
    "$PY" "$ROOT/tests/team/tools/check_harness.py" ;;
  shell)
    "${RUNNER[@]}" run --rm runner bash ;;
  *)
    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
