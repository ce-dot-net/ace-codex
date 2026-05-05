#!/usr/bin/env bash
set -euo pipefail

if ! command -v ace-cli >/dev/null 2>&1; then
  echo "ace-cli not found. Install with: npm install -g @ace-sdk/cli"
  exit 1
fi

AUTH_JSON="$(ace-cli whoami --json 2>/dev/null || echo '{"authenticated":false}')"
IS_AUTH="$(printf '%s' "$AUTH_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("authenticated", False))')"

if [ "$IS_AUTH" = "True" ] || [ "$IS_AUTH" = "true" ]; then
  printf '%s\n' "$AUTH_JSON"
  exit 0
fi

exec ace-cli login --no-browser
