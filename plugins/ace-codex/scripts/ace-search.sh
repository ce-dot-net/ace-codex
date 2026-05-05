#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
shift || true
QUERY="${*:-}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

if [ -z "$QUERY" ]; then
  echo "Usage: $0 [repo-root] <query>"
  exit 1
fi

python3 - "$REPO_ROOT" "$RUNTIME_DIR" "$QUERY" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
runtime_dir = Path(sys.argv[2])
query = sys.argv[3]
sys.path.insert(0, str(runtime_dir))

from ace_cli import search, whoami
from config import load_binding
from ace_codex import render_patterns_context

binding = load_binding(repo_root)
if not binding:
    print("ACE workspace not configured. Create .codex/ace.json first.")
    raise SystemExit(1)

auth = whoami()
if not auth.data or not auth.data.get("authenticated", False):
    print("ACE not authenticated. Run ace login first.")
    raise SystemExit(1)

result = search(query, binding=binding, session_id="manual-search")
patterns = (result.data or {}).get("similar_patterns", []) if result.data else []
if patterns:
    print(render_patterns_context(patterns))
    raise SystemExit(0)

print(result.stderr.strip() or result.stdout.strip() or "No patterns returned.")
raise SystemExit(1)
PY
