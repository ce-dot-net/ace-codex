from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_login_skill_mentions_device_flow():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-login" / "SKILL.md").read_text()
    assert "$ace-login" in text
    assert "ace-cli login --no-browser" in text
    assert "ACE_CLIENT_ID" in text


def test_configure_skill_mentions_codex_binding():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-configure" / "SKILL.md").read_text()
    assert "$ace-configure" in text
    assert ".codex/ace.json" in text
    assert "ace-cli projects list --org <org_id> --json" in text


def test_bootstrap_skill_mentions_status_followup():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-bootstrap" / "SKILL.md").read_text()
    assert "$ace-bootstrap" in text
    assert "ace-cli bootstrap" in text
    assert "ace-cli status --json" in text


def test_review_skill_mentions_session_state_layout():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-review" / "SKILL.md").read_text()
    assert ".codex/.ace-codex/sessions/<session_id>/" in text
    assert "review_result.json" in text
    assert "tool_uses.json" in text


def test_doctor_skill_mentions_status_wrapper():
    text = (ROOT / "plugins" / "ace-codex" / "skills" / "ace-doctor" / "SKILL.md").read_text()
    assert "./plugins/ace-codex/scripts/ace-status.sh" in text
    # The doctor skill should still document the raw `ace-cli status` flag set
    # for manual diagnosis, even when the wrapper is the recommended path.
    assert "ace-cli status --json" in text
    assert "<org_id>" in text and "<project_id>" in text
