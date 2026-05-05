import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS_FILE = ROOT / "plugins" / "ace-codex" / "hooks" / "hooks.json"


def _hook_command(event_name: str) -> str:
    hooks = json.loads(HOOKS_FILE.read_text())
    # Codex's HooksFile schema requires the `{"hooks": {<event>: [...]}}` wrapper.
    return hooks["hooks"][event_name][0]["hooks"][0]["command"]


def test_user_prompt_submit_hook_command_runs_from_repo_root():
    result = subprocess.run(
        _hook_command("UserPromptSubmit"),
        shell=True,
        cwd=ROOT,
        input="{}",
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    # The hook handler produces `{}` for an empty payload.
    assert result.stdout.strip() == "{}"


def test_user_prompt_submit_hook_command_runs_from_workspace_with_installed_cache(tmp_path: Path):
    fake_home = tmp_path / "home"
    cache_root = fake_home / ".codex" / "plugins" / "cache" / "ce-dot-net" / "ace-codex" / "9.9.9"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.symlink(ROOT / "plugins" / "ace-codex" / "runtime", cache_root / "runtime", target_is_directory=True)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(fake_home)

    result = subprocess.run(
        _hook_command("UserPromptSubmit"),
        shell=True,
        cwd=workspace,
        env=env,
        input="{}",
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{}"
