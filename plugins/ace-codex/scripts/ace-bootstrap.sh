#!/usr/bin/env bash
set -euo pipefail

if ! command -v ace-cli >/dev/null 2>&1; then
  echo "ace-cli not found. Install with: npm install -g @ace-sdk/cli"
  exit 1
fi

REPO_ROOT="${1:-$(pwd)}"
if [ "$#" -gt 0 ]; then
  shift
fi
BINDING_FILE="$REPO_ROOT/.codex/ace.json"

if [ -f "$BINDING_FILE" ]; then
  eval "$(python3 - "$BINDING_FILE" <<'PY'
from pathlib import Path
import json
import shlex
import sys

data = json.loads(Path(sys.argv[1]).read_text())
for key, env_key in (("org_id", "ACE_ORG_ID"), ("project_id", "ACE_PROJECT_ID"), ("verbosity", "ACE_VERBOSITY")):
    value = data.get(key)
    if value:
        print(f"export {env_key}={shlex.quote(str(value))}")
PY
)"
fi

if [ -z "${ACE_ORG_ID:-}" ] || [ -z "${ACE_PROJECT_ID:-}" ]; then
  echo "ACE workspace not configured. Create .codex/ace.json first."
  exit 1
fi

MODE="${ACE_BOOTSTRAP_MODE:-hybrid}"
THOROUGHNESS="${ACE_BOOTSTRAP_THOROUGHNESS:-medium}"

exec ace-cli bootstrap \
  --json \
  --mode "$MODE" \
  --thoroughness "$THOROUGHNESS" \
  --org "$ACE_ORG_ID" \
  --project "$ACE_PROJECT_ID" \
  "$@"
