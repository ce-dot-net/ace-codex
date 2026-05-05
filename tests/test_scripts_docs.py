from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_install_doc_mentions_discovery_helpers():
    text = (ROOT / "plugins" / "ace-codex" / "docs" / "INSTALL.md").read_text()
    assert "ace-orgs.sh" in text
    assert "ace-projects.sh" in text
    assert "@ace-codex" in text
    assert "$ace-login" in text
    assert "$ace-doctor" in text
    assert "slash commands" in text
    assert "`/plugins`" not in text
    assert "new thread" in text
    assert "reinstall" in text
    assert "plugin_hooks = true" in text


def test_repo_readme_mentions_config_split():
    text = (ROOT / "README.md").read_text()
    assert "~/.config/ace/config.json" in text
    assert ".codex/ace.json" in text
    assert ".codex/.ace-codex/sessions/<session_id>/" in text
    assert "CODEX_HOME/ace-codex/<workspace-key>/sessions/<session_id>/" in text
    assert ".codex/.ace-codex/workspace/" in text
    assert "CODEX_HOME/ace-codex/<workspace-key>/workspace/" in text
    assert "ACE_CLIENT_ID" in text
    assert "SUPPORT.md" in text
    assert "codex plugin marketplace add ." in text
    assert "@ace-codex" in text
    assert "$ace-status" in text
    assert "slash commands" in text
    assert "`/plugins`" not in text
    assert "reinstall" in text
    assert "new thread" in text


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
