import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(PLUGIN_RUNTIME))

from ace_codex import (  # noqa: E402
    build_review_request,
    classify_prompt_for_search,
    detect_domain_shift,
    has_substantial_work,
    latest_session_state_dir,
    parse_ace_review,
    permission_decision,
    runtime_state_dir,
    session_key,
    session_state_dir,
    search_warning_message,
    should_skip_learning,
    workspace_state_dir,
)


def test_classify_prompt_for_search_detects_impl_work():
    assert classify_prompt_for_search("implement jwt auth in api")
    assert classify_prompt_for_search("add redis caching for token validation")
    assert classify_prompt_for_search("modify auth middleware to rotate refresh tokens")
    assert classify_prompt_for_search("troubleshoot the failing oauth callback handler")
    assert classify_prompt_for_search("hello")
    assert classify_prompt_for_search("what should I build next?")
    assert not classify_prompt_for_search("/ace-status")
    assert not classify_prompt_for_search("$ace-status")


def test_should_skip_learning_filters_trivial_prompts():
    assert should_skip_learning("/ace-status")
    assert should_skip_learning("$ace-status")
    assert not should_skip_learning("hello")
    assert not should_skip_learning("what is this?")
    assert not should_skip_learning("fix broken auth middleware")


def test_has_substantial_work_uses_state_changing_tools():
    assert has_substantial_work(["Read", "Edit"])
    assert not has_substantial_work(["Read", "Glob"])


def test_detect_domain_shift_matches_domain_from_file_path():
    assert detect_domain_shift("src/payments/stripe_client.py", ["payments", "auth"], None) == "payments"
    assert detect_domain_shift("src/payments/stripe_client.py", ["payments", "auth"], "payments") is None
    assert (
        detect_domain_shift(
            "tests/payments/test_stripe_client.py",
            ["payments", "auth"],
            "payments",
            last_file_path="src/payments/stripe_client.py",
        )
        == "payments"
    )


def test_parse_ace_review_extracts_structured_fields():
    parsed = parse_ace_review("ACE_REVIEW: 72% | 5m saved | patterns guided the fix")
    assert parsed is not None
    assert parsed.helpful_pct == 72
    assert parsed.time_saved == "5m saved"
    assert parsed.reason == "patterns guided the fix"


def test_permission_decision_allows_safe_ace_cli():
    assert permission_decision("ace-cli search --json") == "allow"
    assert permission_decision("rm -rf /tmp/x") is None


def test_build_review_request_contains_required_marker():
    prompt = build_review_request(patterns_injected=3, avg_relevance=81, tools_executed=4)
    assert "ACE_REVIEW: N% | Xm saved | one-line reason" in prompt


def test_search_warning_message_mentions_prompt():
    msg = search_warning_message("implement jwt auth")
    assert "implement jwt auth" in msg


def test_session_state_dir_uses_sanitized_session_key(tmp_path: Path):
    path = session_state_dir(tmp_path, "sess 1/root")
    assert path == tmp_path / ".codex" / ".ace-codex" / "sessions" / "sess-1-root"
    assert session_key("  ") == "codex-session"


def test_workspace_state_dir_is_separate_from_sessions(tmp_path: Path):
    assert workspace_state_dir(tmp_path) == tmp_path / ".codex" / ".ace-codex" / "workspace"


def test_runtime_state_dir_falls_back_to_codex_home_when_repo_codex_is_read_only(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    codex_dir = repo_root / ".codex"
    codex_dir.mkdir()
    codex_dir.chmod(0o755)
    (codex_dir / "ace.json").write_text('{"org_id":"org_1","project_id":"prj_1","verbosity":"detailed"}')
    codex_dir.chmod(0o555)
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    expected_prefix = codex_home / "ace-codex"
    runtime_dir = runtime_state_dir(repo_root)
    assert runtime_state_dir(repo_root).is_relative_to(expected_prefix)
    assert session_state_dir(repo_root, "sess-1").is_relative_to(runtime_dir / "sessions")
    assert workspace_state_dir(repo_root).is_relative_to(runtime_dir / "workspace")


def test_latest_session_state_dir_returns_most_recent(tmp_path: Path):
    first = session_state_dir(tmp_path, "sess-a")
    second = session_state_dir(tmp_path, "sess-b")
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    os.utime(first, (1, 1))
    os.utime(second, (2, 2))
    assert latest_session_state_dir(tmp_path) == second
