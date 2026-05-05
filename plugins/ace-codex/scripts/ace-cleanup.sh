#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
MODE="${2:-dry-run}"  # dry-run | delete-sessions | delete-all
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
LOCAL_STATE="$REPO_ROOT/.codex/.ace-codex"

# Resolve CODEX_HOME fallback workspace dir for this repo (sha1 of resolved path).
WORKSPACE_KEY="$(python3 - "$REPO_ROOT" <<'PY'
import hashlib, sys
from pathlib import Path
print(hashlib.sha1(str(Path(sys.argv[1]).resolve()).encode("utf-8")).hexdigest()[:12])
PY
)"
HOME_STATE="$CODEX_HOME_DIR/ace-codex/$WORKSPACE_KEY"

scope() {
    local path="$1"
    [ -d "$path" ] || { echo "  $path: (absent)"; return; }
    local count
    count=$(find "$path" -type f 2>/dev/null | wc -l | tr -d ' ')
    local size
    size=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
    echo "  $path: $count files, $size"
}

echo "ACE local state scopes:"
scope "$LOCAL_STATE"
scope "$HOME_STATE"
echo ""

case "$MODE" in
    dry-run)
        echo "Mode: dry-run (no changes). Re-run with mode = delete-sessions or delete-all to act."
        ;;
    delete-sessions)
        for path in "$LOCAL_STATE/sessions" "$HOME_STATE/sessions"; do
            [ -d "$path" ] || continue
            echo "Removing $path"
            rm -rf "$path"
        done
        echo "Removed sessions/ from local + CODEX_HOME state. workspace/ and ace.json untouched."
        ;;
    delete-all)
        for path in "$LOCAL_STATE" "$HOME_STATE"; do
            [ -d "$path" ] || continue
            echo "Removing $path"
            rm -rf "$path"
        done
        echo "Full local + CODEX_HOME ACE state removed. .codex/ace.json (repo binding) is left intact."
        ;;
    *)
        echo "Unknown mode: $MODE. Use dry-run, delete-sessions, or delete-all." >&2
        exit 2
        ;;
esac
