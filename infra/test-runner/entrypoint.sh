#!/usr/bin/env bash
# Registers the bind-mounted Indico source (editable, no deps) so pytest finds the `indico` plugin entry point,
# prepares the test database extensions, then runs the given command.
set -euo pipefail

if ! python -c "import importlib.metadata as m; m.distribution('indico')" >/dev/null 2>&1; then
  uv pip install --no-deps -e /repo >/dev/null
fi

if [[ -n "${PGHOST:-}" ]]; then
  for _ in $(seq 1 30); do pg_isready -q && break; sleep 1; done
  psql -q -d "${PGDATABASE:-indicotest}" -c 'CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;' >/dev/null
fi

exec "$@"
