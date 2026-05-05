from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_readme_mentions_doctor():
    text = (ROOT / "plugins" / "ace-codex" / "README.md").read_text()
    assert "ace-doctor" in text


def test_install_doc_mentions_doctor():
    text = (ROOT / "plugins" / "ace-codex" / "docs" / "INSTALL.md").read_text()
    assert "ace-doctor" in text
