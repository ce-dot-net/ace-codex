from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_codex_marketplace_add_registers_local_repo_in_temp_home(tmp_path: Path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env.pop("CODEX_HOME", None)

    result = subprocess.run(
        ["codex", "plugin", "marketplace", "add", "."],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    config_path = fake_home / ".codex" / "config.toml"
    assert config_path.exists()
    config = config_path.read_text()
    assert "[marketplaces.ce-dot-net]" in config
    assert f'source = "{ROOT}"' in config
    assert 'source_type = "local"' in config
