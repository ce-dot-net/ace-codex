#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
SESSION_ID="${2:-${ACE_SESSION_ID:-}}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

STATE_DIR=$(python3 - "$REPO_ROOT" "$SESSION_ID" "$RUNTIME_DIR" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
session_id = sys.argv[2] or None
runtime_dir = Path(sys.argv[3])
sys.path.insert(0, str(runtime_dir))

from ace_codex import latest_session_state_dir, session_state_dir

if session_id:
    print(session_state_dir(repo_root, session_id))
else:
    latest = latest_session_state_dir(repo_root)
    print(latest if latest else "")
PY
)

if [ -z "$STATE_DIR" ]; then
  echo '{"pending": false, "message": "No ACE review state found"}'
  exit 0
fi

REVIEW_FILE="$STATE_DIR/review_result.json"
REQUEST_FILE="$STATE_DIR/review_request.json"
RETRIEVAL_FILE="$STATE_DIR/retrieval_state.json"

if [ -f "$REVIEW_FILE" ]; then
  cat "$REVIEW_FILE"
  exit 0
fi

if [ -f "$REQUEST_FILE" ]; then
  echo '{"pending": true, "message": "ACE review request is pending"}'
  exit 0
fi

if [ -f "$RETRIEVAL_FILE" ]; then
  cat "$RETRIEVAL_FILE"
  exit 0
fi

echo '{"pending": false, "message": "No ACE review state found"}'
