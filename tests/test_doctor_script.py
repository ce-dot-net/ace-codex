from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-doctor.sh"


def test_doctor_script_reports_missing_hooks_feature_flag(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true, \"token_status\": \"ok\"}'\n"
        "elif [ \"$cmd\" = \"orgs\" ]; then\n"
        "  echo '{\"count\": 0, \"organizations\": []}'\n"
        "else\n"
        "  echo '{}'\n"
        "fi\n"
    )
    fake_cli.chmod(0o755)

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("model = \"gpt-5\"\n")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run([str(DOCTOR)], cwd=repo_root, env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "codex_hooks_enabled: False" in result.stdout
    assert "codex_hooks_status: missing_plugin_hooks_flag" in result.stdout
    assert "[features].plugin_hooks = true" in result.stdout
    assert "verdict: SET [features].plugin_hooks = true" in result.stdout
