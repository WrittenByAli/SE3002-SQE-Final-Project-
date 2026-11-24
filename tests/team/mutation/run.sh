#!/usr/bin/env bash
# Cosmic Ray mutation campaign. Run only in the Linux test runner with its test DB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CONFIG="$ROOT/tests/team/mutation/cosmic-ray.toml"
REPORTS="$ROOT/tests/team/reports/mutation"
MODE="${1:-final}"
mkdir -p "$REPORTS"

case "$MODE" in
  init|initial)
    SESSION="$REPORTS/area1-initial.sqlite"
    cosmic-ray init "$CONFIG" "$SESSION"
    python "$ROOT/tests/team/mutation/filter_scope.py" "$SESSION"
    if [[ "$MODE" == "initial" ]]; then
      cosmic-ray baseline "$CONFIG"
      cosmic-ray exec "$CONFIG" "$SESSION"
      cr-report "$SESSION" | tee "$REPORTS/cr-report-initial.txt"
      cr-html "$SESSION" > "$REPORTS/initial.html"
    else
      cosmic-ray baseline "$CONFIG"
    fi
    ;;
  run|final)
    SESSION="$REPORTS/area1-final.sqlite"
    cosmic-ray init "$CONFIG" "$SESSION"
    python "$ROOT/tests/team/mutation/filter_scope.py" "$SESSION"
    cosmic-ray baseline "$CONFIG"
    cosmic-ray exec "$CONFIG" "$SESSION"
    cr-report "$SESSION" | tee "$REPORTS/cr-report-final.txt"
    cr-html "$SESSION" > "$REPORTS/final.html"
    ;;
  status)
    SESSION="$REPORTS/area1-final.sqlite"
    cr-report "$SESSION"
    ;;
  status-initial)
    SESSION="$REPORTS/area1-initial.sqlite"
    cr-report "$SESSION"
    ;;
  *)
    printf 'Usage: %s {init|initial|final|run|status|status-initial}\n' "$0" >&2
    exit 2
    ;;
esac
