from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-status.sh"


def test_status_script_forwards_repo_binding_and_client_env(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)
    (repo_root / ".codex").mkdir()
    (repo_root / ".codex" / "ace.json").write_text(
        json.dumps(
            {
                "org_id": "org_1",
                "project_id": "prj_1",
                "verbosity": "detailed",
            }
        )
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_file = tmp_path / "capture.json"
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "shift || true\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true}'\n"
        "  exit 0\n"
        "fi\n"
        "python3 - \"$cmd\" \"$@\" <<'PY'\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "capture = {\n"
        "  'args': sys.argv[1:],\n"
        "  'ACE_ORG_ID': os.environ.get('ACE_ORG_ID'),\n"
        "  'ACE_PROJECT_ID': os.environ.get('ACE_PROJECT_ID'),\n"
        "  'ACE_CLIENT_ID': os.environ.get('ACE_CLIENT_ID'),\n"
        "}\n"
        f"Path({str(capture_file)!r}).write_text(json.dumps(capture))\n"
        "print('{\"playbook\": {}}')\n"
        "PY\n"
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env.pop("ACE_CLIENT_ID", None)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    subprocess.run([str(STATUS)], cwd=repo_root, env=env, check=False, capture_output=True, text=True)

    data = json.loads(capture_file.read_text())
    assert data["args"] == ["status", "--json", "--org", "org_1", "--project", "prj_1"]
    assert data["ACE_ORG_ID"] == "org_1"
    assert data["ACE_PROJECT_ID"] == "prj_1"
    assert data["ACE_CLIENT_ID"] is None


def test_status_script_surfaces_missing_hooks_feature_flag(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)
    (repo_root / ".codex").mkdir()
    (repo_root / ".codex" / "ace.json").write_text(
        json.dumps(
            {
                "org_id": "org_1",
                "project_id": "prj_1",
                "verbosity": "detailed",
            }
        )
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true}'\n"
        "else\n"
        "  echo '{\"playbook\": {}, \"subscription\": null}'\n"
        "fi\n"
    )
    fake_cli.chmod(0o755)

    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("model = \"gpt-5\"\n")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run([str(STATUS)], cwd=repo_root, env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "codex_hooks: missing_plugin_hooks_flag" in result.stdout
    assert "[features].plugin_hooks = true" in result.stdout
