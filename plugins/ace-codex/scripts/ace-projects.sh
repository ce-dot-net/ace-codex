#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
ORG_ID="${ACE_ORG_ID:-${2:-}}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

if [ -z "$ORG_ID" ]; then
  echo "Usage: ACE_ORG_ID=<org_id> $0 [repo-root]"
  exit 1
fi

python3 - "$RUNTIME_DIR" "$ORG_ID" <<'PY'
from pathlib import Path
import sys

runtime_dir = Path(sys.argv[1])
org_id = sys.argv[2]
sys.path.insert(0, str(runtime_dir))

from ace_cli import projects, whoami
from render import format_project_choices

auth = whoami()
if not auth.data or not auth.data.get("authenticated", False):
    print("ACE not authenticated. Run ace login first.")
    raise SystemExit(1)

result = projects(org_id)
if not result.ok or not isinstance(result.data, dict):
    print("ACE project lookup failed.")
    if result.stderr:
        print(result.stderr.strip())
    elif result.stdout:
        print(result.stdout.strip())
    raise SystemExit(1)

print(format_project_choices(result.data))
PY
