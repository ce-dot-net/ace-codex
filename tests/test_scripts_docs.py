from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_install_doc_mentions_discovery_helpers():
    text = (ROOT / "plugins" / "ace-codex" / "docs" / "INSTALL.md").read_text()
    # ACE account prerequisite (repo README and INSTALL.md must both surface this)
    assert "ace-ai.app" in text
    # Discovery + manual fallback path
    assert "ace-orgs.sh" in text
    assert "ace-projects.sh" in text
    # Codex-native invocation
    assert "@ace-codex" in text
    assert "$ace-login" in text
    assert "$ace-doctor" in text
    # The full set of state paths belongs in INSTALL.md, not the user-facing README
    assert ".codex/ace.json" in text
    assert ".codex/.ace-codex/sessions/<session_id>/" in text
    assert "CODEX_HOME" in text and "ace-codex" in text and "<workspace-key>" in text
    assert ".codex/.ace-codex/workspace/" in text
    assert "ACE_CLIENT_ID" in text
    # Hooks feature gate
    assert "plugin_hooks = true" in text
    # Marketplace install command for end users
    assert "codex plugin marketplace add ce-dot-net/ace-codex" in text
    # Reinstall / new-thread guidance for upgrades
    assert "new thread" in text
    assert "reinstall" in text


def test_repo_readme_is_user_facing():
    text = (ROOT / "README.md").read_text()
    # Account prerequisite must be visible in the README itself, not buried
    assert "ace-ai.app" in text
    # Marketplace install command (published form, not the dev-clone form)
    assert "codex plugin marketplace add ce-dot-net/ace-codex" in text
    # User-facing entry points
    assert "@ace-codex" in text
    assert "$ace-login" in text
    assert "$ace-configure" in text
    assert "$ace-doctor" in text
    # Repo binding is the one path users absolutely need to know about
    assert ".codex/ace.json" in text
    # Pointers to deeper docs (so users can find INSTALL/TROUBLESHOOTING)
    assert "SUPPORT.md" in text
    assert "TROUBLESHOOTING.md" in text
    assert "INSTALL.md" in text
    # Hook flag mentioned at least once so users know it exists
    assert "plugin_hooks" in text


def test_plugin_readme_documents_codex_native_invocation():
    text = (ROOT / "plugins" / "ace-codex" / "README.md").read_text()
    assert "@ace-codex" in text
    assert "$ace-configure" in text
    assert "$ace-review" in text
    assert "slash commands" in text
    assert ".codex/.ace-codex/sessions/<session_id>/" in text
    assert "CODEX_HOME/ace-codex/<workspace-key>/sessions/<session_id>/" in text


def test_status_skill_documents_wrapper_usage():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-status" / "SKILL.md").read_text()
    assert "./plugins/ace-codex/scripts/ace-status.sh" in text
    assert "ace-cli status --json" in text
    assert "--org" in text
    assert "--project" in text


def test_example_binding_exists():
    text = (ROOT / "plugins" / "ace-codex" / "docs" / "ace.example.json").read_text()
    assert '"org_id": "org_replace_me"' in text
    assert '"project_id": "prj_replace_me"' in text
    assert '"client_id"' not in text
