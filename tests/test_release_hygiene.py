from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_bundle_ignores_python_artifacts():
    gitignore = (ROOT / ".gitignore").read_text()
    assert "__pycache__/" in gitignore
    assert "*.py[cod]" in gitignore

    pycache_dirs = list((ROOT / "plugins" / "ace-codex").rglob("__pycache__"))
    for path in pycache_dirs:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0


def test_marketplace_entry_matches_plugin_name_and_path():
    marketplace = (ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
    plugin_manifest = (ROOT / "plugins" / "ace-codex" / ".codex-plugin" / "plugin.json").read_text()
    assert '"name": "ace-codex"' in marketplace
    assert '"path": "./plugins/ace-codex"' in marketplace
    assert '"name": "ace-codex"' in plugin_manifest


def test_hooks_and_runtime_do_not_reference_mcp():
    hooks = (ROOT / "plugins" / "ace-codex" / "hooks" / "hooks.json").read_text()
    runtime = (ROOT / "plugins" / "ace-codex" / "runtime" / "ace_codex.py").read_text()
    assert "mcp__" not in hooks
    assert "mcp__" not in runtime
