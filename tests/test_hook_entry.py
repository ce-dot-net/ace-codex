import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(PLUGIN_RUNTIME))

from ace_codex import write_json  # noqa: E402
import hook_entry  # noqa: E402
from hook_entry import (  # noqa: E402
    handle_session_start,
    handle_post_tool_use,
    handle_pre_tool_use,
    handle_stop,
    handle_user_prompt_submit,
)
from ace_codex import runtime_state_dir  # noqa: E402


def _event(tmp_path: Path, **extra):
    event = {"cwd": str(tmp_path), "session_id": "sess_1"}
    event.update(extra)
    return event


def test_hooks_json_uses_fallback_runtime_command():
    hooks = json.loads((ROOT / "plugins" / "ace-codex" / "hooks" / "hooks.json").read_text())
    # Codex's HooksFile expects `{"hooks": {<event>: [...]}}` per
    # codex-rs/config/src/hook_config.rs:HooksFile. Validate that wrapper.
    assert "hooks" in hooks
    command = hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "runtime/hook_entry.py" in command
    # Plugin-cache fallback uses `${CODEX_HOME:-$HOME/.codex}` glob; PLUGIN_ROOT
    # is preferred when Codex sets it inside the hook subprocess env.
    assert "PLUGIN_ROOT" in command
    assert "plugins/cache" in command


def test_user_prompt_submit_blocks_when_workspace_unconfigured(tmp_path: Path):
    result = handle_user_prompt_submit(_event(tmp_path, prompt="implement jwt auth"))
    assert result["decision"] == "block"


def test_user_prompt_submit_sets_retrieval_state_when_configured(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    hook_entry.whoami = lambda: type("R", (), {"data": {"authenticated": True}})()
    hook_entry.search = lambda prompt, binding, session_id=None: type(
        "R", (), {"data": {"similar_patterns": [{"id": "p1", "domain": "auth", "content": "Use JWT", "confidence": 0.9, "helpful": 3}]}}
    )()
    result = handle_user_prompt_submit(_event(tmp_path, prompt="implement jwt auth"))
    assert "hookSpecificOutput" in result
    state = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json").read_text())
    assert state["needs_search"] is False
    assert state["pattern_ids"] == ["p1"]
    domains = json.loads((tmp_path / ".codex" / ".ace-codex" / "workspace" / "domains.json").read_text())
    assert domains["known_domains"] == ["auth"]
    trace = (tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "hook_events.jsonl").read_text().strip().splitlines()
    assert trace
    assert json.loads(trace[-1])["stage"] == "searched"


def test_user_prompt_submit_triggers_search_for_plain_user_prompts(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    hook_entry.whoami = lambda: type("R", (), {"data": {"authenticated": True}})()
    hook_entry.search = lambda prompt, binding, session_id=None: type(
        "R", (), {"data": {"similar_patterns": []}}
    )()

    result = handle_user_prompt_submit(_event(tmp_path, prompt="hello"))

    assert "hookSpecificOutput" in result
    state = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json").read_text())
    assert state["prompt"] == "hello"


def test_user_prompt_submit_falls_back_to_codex_home_when_repo_codex_is_read_only(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    codex_dir = repo_root / ".codex"
    codex_dir.mkdir()
    write_json(codex_dir / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    codex_dir.chmod(0o555)
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    hook_entry.whoami = lambda: type("R", (), {"data": {"authenticated": True}})()
    hook_entry.search = lambda prompt, binding, session_id=None: type(
        "R", (), {"data": {"similar_patterns": [{"id": "p1", "domain": "auth", "content": "Use JWT", "confidence": 0.9, "helpful": 3}]}}
    )()

    result = handle_user_prompt_submit({"cwd": str(repo_root), "session_id": "sess_ro", "prompt": "implement jwt auth"})

    assert "hookSpecificOutput" in result
    state = json.loads((runtime_state_dir(repo_root) / "sessions" / "sess_ro" / "retrieval_state.json").read_text())
    assert state["session_id"] == "sess_ro"
    assert state["pattern_ids"] == ["p1"]


def test_pre_tool_use_blocks_when_retrieval_pending(tmp_path: Path):
    write_json(tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json", {"needs_search": True})
    result = handle_pre_tool_use(_event(tmp_path))
    assert result["decision"] == "block"


def test_pre_tool_use_uses_workspace_root_when_cwd_missing(tmp_path: Path, monkeypatch):
    write_json(tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json", {"needs_search": True})
    runner_dir = tmp_path / "runner"
    runner_dir.mkdir()
    monkeypatch.chdir(runner_dir)

    result = handle_pre_tool_use({"workspace_root": str(tmp_path), "session_id": "sess_1"})

    assert result["decision"] == "block"


def test_pre_tool_use_uses_nested_workspace_root(tmp_path: Path, monkeypatch):
    write_json(tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json", {"needs_search": True})
    runner_dir = tmp_path / "runner-nested"
    runner_dir.mkdir()
    monkeypatch.chdir(runner_dir)

    result = handle_pre_tool_use({"workspace": {"root": str(tmp_path)}, "session_id": "sess_1"})

    assert result["decision"] == "block"


def test_post_tool_use_emits_domain_shift_context(tmp_path: Path):
    write_json(tmp_path / ".codex" / ".ace-codex" / "workspace" / "domains.json", {"known_domains": ["payments"], "last_domain": None})
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    hook_entry.search = lambda query, binding, session_id=None, allowed_domains=None: type(
        "R", (), {"data": {"similar_patterns": [{"id": "p2", "domain": "payments", "content": "Use idempotency", "confidence": 0.8, "helpful": 2}]}}
    )()
    result = handle_post_tool_use(_event(tmp_path, tool_name="Read", tool_input={"file_path": "src/payments/stripe.py"}))
    assert "payments" in result["hookSpecificOutput"]["additionalContext"]


def test_post_tool_use_refreshes_retrieval_for_same_domain_scope_change(tmp_path: Path):
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "workspace" / "domains.json",
        {
            "known_domains": ["payments"],
            "last_domain": "payments",
            "last_file_path": "src/payments/stripe.py",
        },
    )
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    captured = {}

    def fake_search(query, binding, session_id=None, allowed_domains=None):
        captured["query"] = query
        captured["allowed_domains"] = allowed_domains
        return type(
            "R",
            (),
            {"data": {"similar_patterns": [{"id": "p3", "domain": "payments", "content": "Keep fixtures isolated", "confidence": 0.7, "helpful": 1}]}},
        )()

    hook_entry.search = fake_search

    result = handle_post_tool_use(
        _event(tmp_path, tool_name="Read", tool_input={"file_path": "tests/payments/test_stripe.py"})
    )

    assert captured["query"] == "payments test_stripe"
    assert captured["allowed_domains"] == ["payments"]
    assert "payments" in result["hookSpecificOutput"]["additionalContext"]


def test_stop_writes_review_result_when_marker_present(tmp_path: Path):
    result = handle_stop(_event(tmp_path, last_assistant_message="ACE_REVIEW: 75% | 4m saved | useful patterns"))
    assert result == {}
    saved = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "review_result.json").read_text())
    assert saved["helpful_pct"] == 75


def test_stop_calls_real_learning_and_blocks_for_review_when_patterns_used(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json",
        {"prompt": "implement auth", "pattern_ids": ["p1"], "patterns": [{"confidence": 0.8}], "session_id": "sess_1"},
    )
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "tool_uses.json",
        [{"tool_name": "Edit", "tool_input": {"file_path": "a.py"}, "tool_response": {"success": True}, "tool_use_id": "u1", "timestamp": "t"}],
    )
    hook_entry.learn = lambda trace, binding: type("R", (), {"ok": True, "returncode": 0, "stdout": "{}", "stderr": "", "data": {"learning_statistics": {"patterns_created": 1}}})()
    result = handle_stop(_event(tmp_path, last_assistant_message="done"))
    assert result["decision"] == "block"
    learning = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "learning_result.json").read_text())
    assert learning["ok"] is True
    tool_uses = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "tool_uses.json").read_text())
    assert tool_uses == []


def test_stop_calls_learning_even_without_state_changing_tools(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json",
        {"prompt": "hello", "pattern_ids": [], "patterns": [], "session_id": "sess_1"},
    )
    write_json(tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "tool_uses.json", [])
    calls = {}

    def fake_learn(trace, binding):
        calls["trace"] = trace
        return type("R", (), {"ok": True, "returncode": 0, "stdout": "{}", "stderr": "", "data": {"learning_statistics": {"patterns_created": 0}}})()

    hook_entry.learn = fake_learn

    result = handle_stop(_event(tmp_path, last_assistant_message="done"))

    assert result == {}
    assert calls["trace"]["task"] == "hello"
    learning = json.loads((tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "learning_result.json").read_text())
    assert learning["ok"] is True
    trace = (tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "hook_events.jsonl").read_text().strip().splitlines()
    assert json.loads(trace[-1])["stage"] == "learned"


def test_stop_blocks_when_learning_fails_for_substantial_work(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "retrieval_state.json",
        {"prompt": "fix auth", "pattern_ids": ["p1"], "patterns": [{"confidence": 0.5}], "session_id": "sess_1"},
    )
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "tool_uses.json",
        [{"tool_name": "Edit", "tool_input": {"file_path": "a.py"}, "tool_response": {"success": True}, "tool_use_id": "u1", "timestamp": "t"}],
    )
    hook_entry.learn = lambda trace, binding: type("R", (), {"ok": False, "returncode": 1, "stdout": "", "stderr": "learn failed", "data": {}})()

    result = handle_stop(_event(tmp_path, last_assistant_message="done"))

    assert result["decision"] == "block"
    assert "ACE learn failed" in result["reason"]


def test_session_start_surfaces_pending_review_request(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess_1" / "review_request.json",
        {"prompt": "ACE_REVIEW: N% | Xm saved | one-line reason"},
    )

    result = handle_session_start(_event(tmp_path, source="resume"))

    assert "hookSpecificOutput" in result
    assert "ACE_REVIEW" in result["hookSpecificOutput"]["additionalContext"]


def test_session_start_falls_back_to_latest_session_state(tmp_path: Path):
    write_json(tmp_path / ".codex" / "ace.json", {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    write_json(
        tmp_path / ".codex" / ".ace-codex" / "sessions" / "older" / "retrieval_state.json",
        {"prompt": "old prompt", "session_id": "older"},
    )
    latest_dir = tmp_path / ".codex" / ".ace-codex" / "sessions" / "latest"
    write_json(latest_dir / "retrieval_state.json", {"prompt": "latest prompt", "session_id": "latest"})
    latest_dir.touch()

    result = handle_session_start(_event(tmp_path, session_id="fresh", source="resume"))

    assert "latest prompt" in result["hookSpecificOutput"]["additionalContext"]
