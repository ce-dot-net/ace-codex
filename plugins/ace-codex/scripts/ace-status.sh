#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

python3 - "$REPO_ROOT" "$RUNTIME_DIR" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
runtime_dir = Path(sys.argv[2])
sys.path.insert(0, str(runtime_dir))

from ace_cli import status, whoami
from config import load_binding
from ace_codex import latest_session_state_dir, load_json
from render import format_status_report
from workspace import workspace_diagnostics

auth = whoami()
if not auth.data or not auth.data.get("authenticated", False):
    print("ACE not authenticated. Run ace login first.")
    raise SystemExit(1)

binding = load_binding(repo_root)
if not binding:
    print("ACE workspace not configured. Create .codex/ace.json first.")
    raise SystemExit(1)

result = status(binding)
if not result.ok or not isinstance(result.data, dict):
    print("ACE status failed.")
    if result.stderr:
        print(result.stderr.strip())
    elif result.stdout:
        print(result.stdout.strip())
    raise SystemExit(1)

session_dir = latest_session_state_dir(repo_root)
review = load_json(session_dir / "review_result.json", {}) if session_dir else {}
diagnostics = workspace_diagnostics(repo_root)
print(format_status_report(result.data, binding, review, diagnostics.get("hooks")))
PY
