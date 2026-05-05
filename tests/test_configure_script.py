from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGURE = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-configure.sh"


def test_configure_script_writes_binding_and_enables_hooks_feature_flag(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text('model = "gpt-5"\n[notice.model_migrations]\n"foo" = "bar"\n')

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run(
        [str(CONFIGURE), str(repo_root), "org_1", "prj_1"],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    binding = json.loads((repo_root / ".codex" / "ace.json").read_text())
    assert binding == {"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"}
    written_config = (codex_home / "config.toml").read_text()
    assert "[features]" in written_config
    assert "plugin_hooks = true" in written_config
    assert 'model = "gpt-5"' in written_config
    assert '"foo" = "bar"' in written_config
    assert "Enabled Codex hook features" in result.stdout
    assert "runtime state falls back to CODEX_HOME" in result.stdout


def test_configure_script_uses_home_codex_fallback_when_codex_home_unset(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)

    home_dir = tmp_path / "home"
    codex_home = home_dir / ".codex"
    codex_home.mkdir(parents=True)
    (codex_home / "config.toml").write_text("[features]\nexperimental = false\n")

    env = os.environ.copy()
    env.pop("CODEX_HOME", None)
    env["HOME"] = str(home_dir)
    result = subprocess.run(
        [str(CONFIGURE), str(repo_root), "org_1", "prj_1"],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    written_config = (codex_home / "config.toml").read_text()
    assert "experimental = false" in written_config
    assert "plugin_hooks = true" in written_config
    assert "Enabled Codex hook features" in result.stdout
    assert "runtime state falls back to CODEX_HOME" in result.stdout


def test_configure_script_only_updates_features_section(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        "[custom]\n"
        "plugin_hooks = false\n"
        "[features]\n"
        "experimental = true\n"
    )

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run(
        [str(CONFIGURE), str(repo_root), "org_1", "prj_1"],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    written_config = (codex_home / "config.toml").read_text()
    assert "[custom]\nplugin_hooks = false" in written_config
    assert "[features]\nplugin_hooks = true\nexperimental = true" in written_config
