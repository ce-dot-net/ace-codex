#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

python3 - "$RUNTIME_DIR" <<'PY'
from pathlib import Path
import sys

runtime_dir = Path(sys.argv[1])
sys.path.insert(0, str(runtime_dir))

from ace_cli import orgs, whoami
from render import format_org_choices

auth = whoami()
if not auth.data or not auth.data.get("authenticated", False):
    print("ACE not authenticated. Run ace login first.")
    raise SystemExit(1)

result = orgs()
if not result.ok or not isinstance(result.data, dict):
    print("ACE organizations lookup failed.")
    if result.stderr:
        print(result.stderr.strip())
    elif result.stdout:
        print(result.stdout.strip())
    raise SystemExit(1)

print(format_org_choices(result.data))
PY
