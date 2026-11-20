#!/usr/bin/env bash
# Full reset of the local Indico test environment: wipes DB + Redis + files, recreates schema, re-seeds.
# Usage (from repo root):  bash tests/team/seed/reset.sh
# Output: tests/team/.env.test (gitignored) with room id + API tokens for the test suites.
set -euo pipefail
export MSYS_NO_PATHCONV=1          # stop Git Bash on Windows from rewriting container paths

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
COMPOSE_DIR="$ROOT/infra/indico-containers/indico-prod"
OUT="$ROOT/tests/team/.env.test"

cd "$COMPOSE_DIR"
docker compose down -v --remove-orphans          # -v drops postgres, redis and file volumes
docker compose up -d

echo "Waiting for Indico on http://localhost:8081 ..."
for _ in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8081/ || true)
  [[ "$code" == "200" || "$code" == "302" ]] && break
  sleep 5
done
[[ "$code" == "200" || "$code" == "302" ]] || { echo "Indico did not come up (last HTTP $code)"; exit 1; }

json=$(docker compose exec -T indico-web /opt/indico/.venv/bin/python - < "$ROOT/tests/team/seed/seed_rb.py" 2>/dev/null | tail -1)
OUT_NATIVE="$OUT"; command -v cygpath >/dev/null && OUT_NATIVE="$(cygpath -w "$OUT")"   # Windows Python needs D:\ paths
python - "$json" "$OUT_NATIVE" <<'PY'
import json, sys
d = json.loads(sys.argv[1])
with open(sys.argv[2], 'w') as f:
    f.write(f"INDICO_BASE_URL=http://localhost:8081\n")
    f.write(f"ROOM_ID={d['room_id']}\n")
    f.write(f"USER1_TOKEN={d['tokens']['user1']}\n")
    f.write(f"MGR1_TOKEN={d['tokens']['mgr1']}\n")
print(f"Seeded: room_id={d['room_id']} users={d['users']}")
PY
echo "Wrote $OUT"
