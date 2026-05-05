from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNTIME = ROOT / "plugins" / "ace-codex" / "runtime"
sys.path.insert(0, str(PLUGIN_RUNTIME))

from config import codex_hooks_status, load_binding, save_binding  # noqa: E402


def test_save_and_load_binding(tmp_path: Path):
    saved = save_binding(tmp_path, "org_1", "prj_1", "compact")
    assert saved["org_id"] == "org_1"
    loaded = load_binding(tmp_path)
    assert loaded == {"org_id": "org_1", "project_id": "prj_1", "verbosity": "compact"}


def test_codex_hooks_status_detects_missing_plugin_hooks_flag(tmp_path: Path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("model = \"gpt-5\"\n")
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    status = codex_hooks_status()

    assert status["enabled"] is False
    assert status["status"] == "missing_plugin_hooks_flag"
    assert status["user_hooks_enabled"] is True
    assert status["plugin_hooks_enabled"] is False
    assert str(codex_home / "config.toml") == status["config_path"]
    assert "[features].plugin_hooks = true" in status["message"]


def test_codex_hooks_status_detects_both_flags_enabled(tmp_path: Path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("[features]\nplugin_hooks = true\n")
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    status = codex_hooks_status()

    assert status["enabled"] is True
    assert status["status"] == "enabled"
    assert status["user_hooks_enabled"] is True
    assert status["plugin_hooks_enabled"] is True


def test_ensure_codex_hooks_enabled_writes_plugin_hooks_without_clobbering_config(tmp_path: Path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    config_path = codex_home / "config.toml"
    config_path.write_text('model = "gpt-5.4"\n[notice.model_migrations]\n"foo" = "bar"\n')
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    from config import ensure_codex_hooks_enabled  # noqa: E402

    result = ensure_codex_hooks_enabled()
    written = config_path.read_text()

    assert result["enabled"] is True
    assert "[features]" in written
    assert "plugin_hooks = true" in written
    assert 'model = "gpt-5.4"' in written
    assert '"foo" = "bar"' in written


def test_ensure_codex_hooks_enabled_uses_home_codex_fallback_when_codex_home_unset(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    config_path = codex_home / "config.toml"
    config_path.write_text("[features]\nexperimental = false\n")

    from config import ensure_codex_hooks_enabled  # noqa: E402

    result = ensure_codex_hooks_enabled()
    written = config_path.read_text()

    assert result["enabled"] is True
    assert result["config_path"] == str(config_path)
    assert "experimental = false" in written
    assert "plugin_hooks = true" in written


def test_ensure_codex_hooks_enabled_only_updates_features_section(tmp_path: Path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    config_path = codex_home / "config.toml"
    config_path.write_text(
        "[custom]\n"
        "plugin_hooks = false\n"
        "[features]\n"
        "experimental = true\n"
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    from config import ensure_codex_hooks_enabled  # noqa: E402

    result = ensure_codex_hooks_enabled()
    written = config_path.read_text()

    assert result["enabled"] is True
    assert "[custom]\nplugin_hooks = false" in written
    assert "[features]\nplugin_hooks = true\nexperimental = true" in written
