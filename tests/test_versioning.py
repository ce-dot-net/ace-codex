from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_manifest_has_semver_version():
    manifest = json.loads((ROOT / "plugins" / "ace-codex" / ".codex-plugin" / "plugin.json").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


def test_versioning_doc_explains_release_policy():
    text = (ROOT / "plugins" / "ace-codex" / "docs" / "VERSIONING.md").read_text()
    assert "semantic versioning" in text
    assert "plugin.json" in text
    assert "CHANGELOG.md" in text


def test_plugin_manifest_advertises_codex_native_entrypoints():
    manifest = json.loads((ROOT / "plugins" / "ace-codex" / ".codex-plugin" / "plugin.json").read_text())
    interface = manifest["interface"]

    assert "@ace-codex" in interface["longDescription"]
    assert any("@ace-codex" in prompt for prompt in interface["defaultPrompt"])
    assert any("$ace-" in prompt for prompt in interface["defaultPrompt"])


def test_plugin_manifest_links_to_public_policy_docs():
    manifest = json.loads((ROOT / "plugins" / "ace-codex" / ".codex-plugin" / "plugin.json").read_text())
    interface = manifest["interface"]

    assert interface["privacyPolicyURL"].endswith("/PRIVACY.md")
    assert interface["termsOfServiceURL"].endswith("/TERMS.md")
