from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGIN = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-login.sh"


def test_login_script_returns_existing_auth_state(tmp_path: Path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true, \"user\": {\"email\": \"user@example.com\"}}'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    result = subprocess.run([str(LOGIN)], env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert '"authenticated": true' in result.stdout


def test_login_script_falls_through_to_device_login(tmp_path: Path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": false}'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"--no-browser\" ]; then\n"
        "  echo 'device login started'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    result = subprocess.run([str(LOGIN)], env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "device login started" in result.stdout
