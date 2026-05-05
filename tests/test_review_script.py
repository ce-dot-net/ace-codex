from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-review.sh"
RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(RUNTIME))

from ace_codex import runtime_state_dir  # noqa: E402


def _prepare_repo(repo_root: Path) -> None:
    plugin_runtime = repo_root / "plugins" / "ace-codex" / "runtime"
    plugin_runtime.parent.mkdir(parents=True, exist_ok=True)
    plugin_runtime.symlink_to(RUNTIME)


def test_review_script_reads_latest_session_state(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _prepare_repo(repo_root)
    older = repo_root / ".codex" / ".ace-codex" / "sessions" / "older"
    latest = repo_root / ".codex" / ".ace-codex" / "sessions" / "latest"
    older.mkdir(parents=True)
    latest.mkdir(parents=True)
    (older / "review_result.json").write_text(json.dumps({"helpful_pct": 50}))
    (latest / "review_result.json").write_text(json.dumps({"helpful_pct": 90}))
    latest.touch()

    result = subprocess.run([str(REVIEW), str(repo_root)], check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert json.loads(result.stdout)["helpful_pct"] == 90


def test_review_script_reads_explicit_session_id(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _prepare_repo(repo_root)
    session_dir = repo_root / ".codex" / ".ace-codex" / "sessions" / "sess_1"
    session_dir.mkdir(parents=True)
    (session_dir / "review_request.json").write_text(json.dumps({"prompt": "ACE_REVIEW"}))

    result = subprocess.run([str(REVIEW), str(repo_root), "sess_1"], check=False, capture_output=True, text=True)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["pending"] is True


def test_review_script_reads_fallback_session_state_from_codex_home_when_repo_codex_is_read_only(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _prepare_repo(repo_root)
    codex_dir = repo_root / ".codex"
    codex_dir.mkdir()
    codex_dir.chmod(0o755)
    (codex_dir / "ace.json").write_text(json.dumps({"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"}))
    codex_dir.chmod(0o555)
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    session_dir = runtime_state_dir(repo_root) / "sessions" / "sess_home"
    session_dir.mkdir(parents=True)
    (session_dir / "review_result.json").write_text(json.dumps({"helpful_pct": 88}))

    result = subprocess.run([str(REVIEW), str(repo_root), "sess_home"], check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert json.loads(result.stdout)["helpful_pct"] == 88
