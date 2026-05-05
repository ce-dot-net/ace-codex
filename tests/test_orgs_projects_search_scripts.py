from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORGS = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-orgs.sh"
PROJECTS = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-projects.sh"
SEARCH = ROOT / "plugins" / "ace-codex" / "scripts" / "ace-search.sh"


def _repo_with_runtime(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_dir = ROOT / "plugins" / "ace-codex" / "runtime"
    (repo_root / "plugins" / "ace-codex").mkdir(parents=True)
    (repo_root / "plugins" / "ace-codex" / "runtime").symlink_to(runtime_dir)
    return repo_root


def test_orgs_script_renders_org_list(tmp_path: Path):
    repo_root = _repo_with_runtime(tmp_path)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true}'\n"
        "elif [ \"$cmd\" = \"orgs\" ]; then\n"
        "  echo '{\"count\": 1, \"organizations\": [{\"org_id\": \"org_1\", \"name\": \"Org One\"}]}'\n"
        "else\n"
        "  echo '{}'\n"
        "fi\n"
    )
    fake_cli.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run([str(ORGS), str(repo_root)], env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "Org One" in result.stdout
    assert "org_1" in result.stdout


def test_projects_script_renders_project_list(tmp_path: Path):
    repo_root = _repo_with_runtime(tmp_path)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true}'\n"
        "elif [ \"$cmd\" = \"projects\" ]; then\n"
        "  echo '{\"count\": 1, \"projects\": [{\"project_id\": \"prj_1\", \"name\": \"Project One\"}]}'\n"
        "else\n"
        "  echo '{}'\n"
        "fi\n"
    )
    fake_cli.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["ACE_ORG_ID"] = "org_1"

    result = subprocess.run([str(PROJECTS), str(repo_root)], env=env, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "Project One" in result.stdout
    assert "prj_1" in result.stdout


def test_search_script_renders_patterns_from_binding(tmp_path: Path):
    repo_root = _repo_with_runtime(tmp_path)
    (repo_root / ".codex").mkdir()
    (repo_root / ".codex" / "ace.json").write_text(
        json.dumps({"org_id": "org_1", "project_id": "prj_1", "verbosity": "detailed"})
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_cli = fake_bin / "ace-cli"
    fake_cli.write_text(
        "#!/usr/bin/env bash\n"
        "cmd=\"$1\"\n"
        "if [ \"$cmd\" = \"whoami\" ]; then\n"
        "  echo '{\"authenticated\": true}'\n"
        "elif [ \"$cmd\" = \"search\" ]; then\n"
        "  echo '{\"similar_patterns\": [{\"id\": \"p1\", \"domain\": \"auth\", \"content\": \"Use JWT refresh rotation\", \"confidence\": 0.9, \"helpful\": 2}]}'\n"
        "else\n"
        "  echo '{}'\n"
        "fi\n"
    )
    fake_cli.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        [str(SEARCH), str(repo_root), "implement", "auth"],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Use JWT refresh rotation" in result.stdout
    assert "auth" in result.stdout
