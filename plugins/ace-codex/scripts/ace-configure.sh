#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
ORG_ID="${ACE_ORG_ID:-${2:-}}"
PROJECT_ID="${ACE_PROJECT_ID:-${3:-}}"
VERBOSITY="${ACE_VERBOSITY:-detailed}"

if [ -z "$ORG_ID" ] || [ -z "$PROJECT_ID" ]; then
  echo "Usage: ACE_ORG_ID=<org> ACE_PROJECT_ID=<project> $0 [repo-root]"
  echo ""
  echo "Discovery helpers:"
  echo "  ./plugins/ace-codex/scripts/ace-orgs.sh"
  echo "  ACE_ORG_ID=<org_id> ./plugins/ace-codex/scripts/ace-projects.sh"
  exit 1
fi

mkdir -p "$REPO_ROOT/.codex"
python3 - "$REPO_ROOT" "$ORG_ID" "$PROJECT_ID" "$VERBOSITY" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / "plugins" / "ace-codex" / "runtime"))
from config import ensure_codex_hooks_enabled, save_binding

repo_root = Path(sys.argv[1])
save_binding(repo_root, sys.argv[2], sys.argv[3], sys.argv[4])
hooks = ensure_codex_hooks_enabled()
print(f"Wrote {repo_root}/.codex/ace.json")
print(hooks.get("message", "Codex hooks are enabled."))
print("ACE runtime state falls back to CODEX_HOME automatically when repo-local .codex is not writable.")
PY
