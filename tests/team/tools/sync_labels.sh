#!/usr/bin/env bash
# Create/update the repository labels from .github/labels.yml (idempotent). Needs: gh (logged in, write access), python + PyYAML.
#   bash tests/team/tools/sync_labels.sh [owner/repo]
set -euo pipefail
REPO="${1:-WrittenByAli/SE3002-SQE-Final-Project-}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LABELS="$ROOT/.github/labels.yml"
command -v cygpath >/dev/null && LABELS="$(cygpath -m "$LABELS")"
python -c "import sys,yaml; [print(l['name'], l['color'], l['description'], sep='\t') for l in yaml.safe_load(open(sys.argv[1]))]" "$LABELS" |
while IFS=$'\t' read -r name color desc; do
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null
  echo "label: $name"
done
