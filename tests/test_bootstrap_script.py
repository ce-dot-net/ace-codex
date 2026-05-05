from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-bootstrap.sh"


def test_bootstrap_script_forwards_repo_binding_and_client_env(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".codex").mkdir()
    (repo_root / ".codex" / "ace.json").write_text(
        json.dumps(
            {
                "org_id": "org_1",
                "project_id": "prj_1",
                "verbosity": "compact",
            }
        )
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_file = tmp_path / "capture.json"
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "python3 - \"$@\" <<'PY'\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "capture = {\n"
        "  'args': sys.argv[1:],\n"
        "  'ACE_ORG_ID': os.environ.get('ACE_ORG_ID'),\n"
        "  'ACE_PROJECT_ID': os.environ.get('ACE_PROJECT_ID'),\n"
        "  'ACE_CLIENT_ID': os.environ.get('ACE_CLIENT_ID'),\n"
        "}\n"
        f"Path({str(capture_file)!r}).write_text(json.dumps(capture))\n"
        "print('{}')\n"
        "PY\n"
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env.pop("ACE_CLIENT_ID", None)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    subprocess.run([str(BOOTSTRAP)], cwd=repo_root, env=env, check=False, capture_output=True, text=True)

    data = json.loads(capture_file.read_text())
    assert data["args"][:4] == ["bootstrap", "--json", "--mode", "hybrid"]
    assert "--thoroughness" in data["args"]
    assert "medium" in data["args"]
    assert data["ACE_ORG_ID"] == "org_1"
    assert data["ACE_PROJECT_ID"] == "prj_1"
    assert data["ACE_CLIENT_ID"] is None


def test_bootstrap_script_does_not_forward_repo_root_argument(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".codex").mkdir()
    (repo_root / ".codex" / "ace.json").write_text(
        json.dumps(
            {
                "org_id": "org_1",
                "project_id": "prj_1",
                "verbosity": "compact",
            }
        )
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture_file = tmp_path / "capture-positional.json"
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "python3 - \"$@\" <<'PY'\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        f"Path({str(capture_file)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        "print('{}')\n"
        "PY\n"
    )
    fake_cli.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    subprocess.run([str(BOOTSTRAP), str(repo_root)], cwd=repo_root, env=env, check=False, capture_output=True, text=True)

    args = json.loads(capture_file.read_text())
    assert str(repo_root) not in args
