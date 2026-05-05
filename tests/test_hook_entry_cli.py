from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_ENTRY = ROOT / "plugins" / "ace-codex" / "runtime" / "hook_entry.py"


def _run_hook(handler: str, payload: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(HOOK_ENTRY), handler],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout or "{}")


def test_hook_entry_cli_blocks_unconfigured_user_prompt(tmp_path: Path):
    payload = {
        "cwd": str(tmp_path),
        "session_id": "sess_cli",
        "prompt": "implement jwt auth",
        "hook_event_name": "UserPromptSubmit",
    }

    result = _run_hook("user_prompt_submit", payload)

    assert result["decision"] == "block"
    assert "ACE workspace not configured" in result["reason"]


def test_hook_entry_cli_blocks_pre_tool_use_when_retrieval_pending(tmp_path: Path):
    state_dir = tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_cli"
    state_dir.mkdir(parents=True)
    (state_dir / "retrieval_state.json").write_text(json.dumps({"needs_search": True}))
    payload = {
        "cwd": str(tmp_path),
        "session_id": "sess_cli",
        "tool_name": "Edit",
        "hook_event_name": "PreToolUse",
    }

    result = _run_hook("pre_tool_use", payload)

    assert result["decision"] == "block"
    assert "ACE retrieval must run before state-changing work" in result["reason"]
