from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(PLUGIN_RUNTIME))

import ace_cli  # noqa: E402


def test_base_env_sets_binding_fields(monkeypatch):
    monkeypatch.delenv("ACE_CLIENT_ID", raising=False)
    env = ace_cli._base_env({"org_id": "org_1", "project_id": "prj_1", "verbosity": "compact"})
    assert env["ACE_ORG_ID"] == "org_1"
    assert env["ACE_PROJECT_ID"] == "prj_1"
    assert env["ACE_VERBOSITY"] == "compact"
    assert "ACE_CLIENT_ID" not in env


def test_base_env_preserves_caller_client_id(monkeypatch):
    monkeypatch.setenv("ACE_CLIENT_ID", "codex-custom")
    env = ace_cli._base_env({"org_id": "org_1", "project_id": "prj_1"})
    assert env["ACE_CLIENT_ID"] == "codex-custom"


def test_search_builds_pin_and_allowed_domains(monkeypatch):
    captured = {}

    def fake_run_json(args, binding=None, stdin_text=None, timeout=30):
        captured["args"] = args
        captured["binding"] = binding
        captured["stdin_text"] = stdin_text
        captured["timeout"] = timeout
        return ace_cli.CLIResult(True, 0, "{}", "", {})

    monkeypatch.setattr(ace_cli, "run_json", fake_run_json)
    ace_cli.search("implement auth", {"org_id": "org", "project_id": "prj"}, session_id="sess_1", allowed_domains=["auth"])
    assert captured["args"] == ["search", "--stdin", "--json", "--pin-session", "sess_1", "--allowed-domains", "auth"]
    assert captured["stdin_text"] == "implement auth"


def test_learn_uses_transcript_file_not_stdin(monkeypatch, tmp_path):
    captured = {}

    def fake_run_json(args, binding=None, stdin_text=None, timeout=30):
        captured["args"] = args
        captured["binding"] = binding
        captured["stdin_text"] = stdin_text
        captured["timeout"] = timeout
        return ace_cli.CLIResult(True, 0, "{}", "", {})

    monkeypatch.setattr(ace_cli, "run_json", fake_run_json)
    ace_cli.learn({"task": "x"}, {"org_id": "org", "project_id": "prj", "verbosity": "compact"})
    assert "--json" not in captured["args"]
    assert "--stdin" not in captured["args"]
    assert "--transcript" in captured["args"]
    assert captured["stdin_text"] is None
    assert "--verbosity" in captured["args"]
    assert "compact" in captured["args"]


def test_extract_codex_file_paths_apply_patch():
    sys.path.insert(0, str(PLUGIN_RUNTIME))
    import ace_codex
    patch = """*** Begin Patch
*** Update File: src/auth/jwt.py
@@
-x
+y
*** Add File: tests/test_jwt.py
hello
*** End Patch"""
    paths = ace_codex.extract_codex_file_paths("apply_patch", {"command": patch})
    assert paths == ["src/auth/jwt.py", "tests/test_jwt.py"]


def test_extract_codex_file_paths_bash():
    sys.path.insert(0, str(PLUGIN_RUNTIME))
    import ace_codex
    paths = ace_codex.extract_codex_file_paths("Bash", {"command": "sed -n '1,5p' /tmp/foo/bar.py"})
    assert paths == ["/tmp/foo/bar.py"]


def test_extract_codex_file_paths_handles_missing_command():
    sys.path.insert(0, str(PLUGIN_RUNTIME))
    import ace_codex
    assert ace_codex.extract_codex_file_paths("apply_patch", {}) == []
    assert ace_codex.extract_codex_file_paths("Bash", {"command": ["ls"]}) == []

