from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(PLUGIN_RUNTIME))

from render import format_org_choices, format_project_choices, format_status_report  # noqa: E402


def test_format_status_report_contains_key_fields():
    report = format_status_report(
        {"playbook": {"total_patterns": 4, "helpful_total": 7, "harmful_total": 1}, "subscription": {"plan": "pro", "usage": {"patterns": {"used": 2, "limit": 100}}}},
        {"org_id": "org_1", "project_id": "prj_1", "verbosity": "compact"},
        {"helpful_pct": 75, "time_saved": "4m saved", "reason": "useful"},
    )
    assert "org_id: org_1" in report
    assert "patterns_total: 4" in report
    assert "last_review_helpful_pct: 75" in report


def test_format_status_report_handles_null_subscription_and_renders_hooks_warning():
    report = format_status_report(
        {"playbook": {"total_patterns": 1}, "subscription": None},
        {"org_id": "org_1", "project_id": "prj_1", "verbosity": "compact"},
        {},
        {
            "enabled": False,
            "config_path": "/tmp/codex/config.toml",
            "hooks_file_path": "/tmp/codex/hooks.json",
            "status": "missing_feature_flag",
            "message": "Codex hooks are disabled. Set [features].codex_hooks = true in /tmp/codex/config.toml.",
        },
    )
    assert "plan: -" in report
    assert "pattern_usage: 0/0" in report
    assert "codex_hooks: missing_feature_flag" in report
    assert "[features].codex_hooks = true" in report


def test_format_org_choices_formats_lines():
    text = format_org_choices({"organizations": [{"name": "ce-dot-net", "org_id": "org_1"}]})
    assert "ce-dot-net" in text
    assert "org_1" in text


def test_format_project_choices_formats_lines():
    text = format_project_choices({"projects": [{"project_name": "ace-codex", "project_id": "prj_1"}]})
    assert "ace-codex" in text
    assert "prj_1" in text
