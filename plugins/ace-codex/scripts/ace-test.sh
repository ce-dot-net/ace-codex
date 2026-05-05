#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
BINDING_FILE="$REPO_ROOT/.codex/ace.json"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
CODEX_CONFIG="$CODEX_HOME_DIR/config.toml"
SESSIONS_DIR="$REPO_ROOT/.codex/.ace-codex/sessions"

fail() { echo "FAIL: $1"; exit 1; }
pass() { echo "PASS: $1"; }

command -v ace-cli >/dev/null 2>&1 || fail "ace-cli not on PATH (run \$ace-install-cli)"
pass "ace-cli on PATH ($(ace-cli --version 2>/dev/null || echo unknown))"

command -v python3 >/dev/null 2>&1 || fail "python3 not available (required by hook runtime)"
pass "python3 on PATH ($(python3 --version 2>&1))"

if [ ! -f "$BINDING_FILE" ]; then
    fail "$BINDING_FILE missing (run \$ace-configure)"
fi
python3 - "$BINDING_FILE" <<'PY' || fail ".codex/ace.json missing org_id or project_id"
import json, sys
data = json.load(open(sys.argv[1]))
assert data.get("org_id"), "missing org_id"
assert data.get("project_id"), "missing project_id"
PY
pass ".codex/ace.json has org_id and project_id"

if [ -f "$CODEX_CONFIG" ] && grep -qE "^\s*plugin_hooks\s*=\s*true" "$CODEX_CONFIG"; then
    pass "[features].plugin_hooks = true in $CODEX_CONFIG"
else
    fail "[features].plugin_hooks = true missing in $CODEX_CONFIG (run \$ace-configure)"
fi

if [ -d "$SESSIONS_DIR" ] && find "$SESSIONS_DIR" -name "hook_events.jsonl" -type f | head -1 | grep -q .; then
    pass "recent hook fire log present under $SESSIONS_DIR"
else
    echo "WARN: no hook event log found yet under $SESSIONS_DIR. Hooks fire only after a real Codex session."
fi

echo "verdict: ok"
