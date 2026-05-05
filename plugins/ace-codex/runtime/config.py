from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from ace_codex import (
    hook_events_path,
    latest_session_state_dir,
    load_json,
    repo_config_path,
    sessions_state_dir,
    write_json,
)


def load_binding(repo_root: Path) -> dict:
    return load_json(repo_config_path(repo_root), {})


def save_binding(repo_root: Path, org_id: str, project_id: str, verbosity: str = "detailed") -> dict:
    payload = {
        "org_id": org_id,
        "project_id": project_id,
        "verbosity": verbosity,
    }
    write_json(repo_config_path(repo_root), payload)
    return payload


def binding_exists(repo_root: Path) -> bool:
    data = load_binding(repo_root)
    return bool(data.get("org_id") and data.get("project_id"))


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def codex_config_path() -> Path:
    return codex_home() / "config.toml"


def codex_hooks_file_path() -> Path:
    return codex_home() / "hooks.json"


def _load_codex_user_config(path: Path) -> dict:
    if not path.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(path.read_text())
    except Exception:
        return {}


def codex_hooks_status() -> dict:
    """
    Codex has two separate hook feature flags:
      - `hooks` (alias `codex_hooks`): Stable, default ON. Loads `~/.codex/hooks.json`
        and `<repo>/.codex/hooks.json`.
      - `plugin_hooks`: UnderDevelopment, default OFF. Loads plugin-bundled
        `hooks/hooks.json` referenced from a plugin's manifest.

    Plugin-bundled hooks (which the ACE Codex plugin uses) are silently ignored
    unless `[features].plugin_hooks = true` is set. The codex_hooks alias by
    itself does not enable plugin-bundled hooks.
    """
    config_path = codex_config_path()
    hooks_file_path = codex_hooks_file_path()
    config = _load_codex_user_config(config_path)
    features = config.get("features") or {}
    # `hooks` is the canonical key; `codex_hooks` is the deprecated alias. Default ON.
    user_set_hooks = features.get("hooks")
    if user_set_hooks is None:
        user_set_hooks = features.get("codex_hooks")
    user_hooks_enabled = True if user_set_hooks is None else bool(user_set_hooks)
    plugin_hooks_enabled = bool(features.get("plugin_hooks"))

    enabled = user_hooks_enabled and plugin_hooks_enabled
    if not user_hooks_enabled:
        status = "user_hooks_disabled"
        message = (
            f"User-level hooks are disabled. Remove `hooks = false` (or `codex_hooks = false`) "
            f"from [features] in {config_path} to restore the default."
        )
    elif not plugin_hooks_enabled:
        status = "missing_plugin_hooks_flag"
        message = (
            f"Plugin-bundled hooks are gated. Set [features].plugin_hooks = true in {config_path} "
            f"and restart Codex so the ACE plugin's hooks/hooks.json is honored."
        )
    else:
        status = "enabled"
        message = f"Codex hook features (hooks + plugin_hooks) are enabled in {config_path}."
    return {
        "enabled": enabled,
        "status": status,
        "message": message,
        "config_path": str(config_path),
        "hooks_file_path": str(hooks_file_path),
        "hooks_file_present": hooks_file_path.exists(),
        "user_hooks_enabled": user_hooks_enabled,
        "plugin_hooks_enabled": plugin_hooks_enabled,
    }


def _replace_or_insert_features_flag(existing: str, key: str, value: str = "true") -> str:
    lines = existing.splitlines(keepends=True)
    features_index = next((i for i, line in enumerate(lines) if re.match(r"^\[features\]\s*$", line)), None)
    if features_index is None:
        suffix = "" if not existing or existing.endswith("\n") else "\n"
        return f"{existing}{suffix}[features]\n{key} = {value}\n"

    section_end = len(lines)
    for index in range(features_index + 1, len(lines)):
        if re.match(r"^\[[^\n]+\]\s*$", lines[index]):
            section_end = index
            break

    key_pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(features_index + 1, section_end):
        if key_pattern.match(lines[index]):
            lines[index] = re.sub(rf"^(\s*{re.escape(key)}\s*=\s*).*$", rf"\g<1>{value}\n", lines[index], count=1)
            return "".join(lines)

    lines.insert(features_index + 1, f"{key} = {value}\n")
    return "".join(lines)


def cached_plugin_versions(plugin_name: str = "ace-codex") -> list[dict]:
    cache_root = codex_home() / "plugins" / "cache"
    if not cache_root.exists():
        return []
    found: list[dict] = []
    for marketplace_dir in sorted(cache_root.iterdir()):
        if not marketplace_dir.is_dir():
            continue
        plugin_dir = marketplace_dir / plugin_name
        if not plugin_dir.is_dir():
            continue
        for version_dir in sorted(plugin_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            manifest = version_dir / ".codex-plugin" / "plugin.json"
            data = load_json(manifest, {}) if manifest.exists() else {}
            found.append(
                {
                    "marketplace": marketplace_dir.name,
                    "plugin": plugin_name,
                    "version": data.get("version") or version_dir.name,
                    "path": str(version_dir),
                    "manifest_present": manifest.exists(),
                }
            )
    return found


def repo_plugin_manifest_version(repo_root: Path, plugin_name: str = "ace-codex") -> str | None:
    manifest = repo_root / "plugins" / plugin_name / ".codex-plugin" / "plugin.json"
    data = load_json(manifest, {}) if manifest.exists() else {}
    return data.get("version")


def codex_plugin_enabled(plugin_name: str = "ace-codex") -> dict:
    config_path = codex_config_path()
    config = _load_codex_user_config(config_path)
    plugins = config.get("plugins") or {}
    matches: list[dict] = []
    for key, value in plugins.items():
        head = key.split("@", 1)[0]
        if head == plugin_name:
            matches.append({"key": key, "enabled": bool((value or {}).get("enabled"))})
    return {
        "any_match": bool(matches),
        "any_enabled": any(item["enabled"] for item in matches),
        "entries": matches,
        "config_path": str(config_path),
    }


def recent_hook_events(repo_root: Path, limit: int = 50) -> list[dict]:
    sessions_dir = sessions_state_dir(repo_root)
    if not sessions_dir.exists():
        return []
    events: list[dict] = []
    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir():
            continue
        log_path = session_dir / "hook_events.jsonl"
        if not log_path.exists():
            continue
        for raw in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except Exception:
                continue
    events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return events[:limit]


def hook_fire_summary(repo_root: Path) -> dict:
    events = recent_hook_events(repo_root, limit=200)
    if not events:
        return {"event_count": 0, "last_timestamp": None, "by_handler": {}}
    by_handler: dict[str, int] = {}
    for event in events:
        handler = event.get("handler") or event.get("hook_event_name") or "unknown"
        by_handler[handler] = by_handler.get(handler, 0) + 1
    return {
        "event_count": len(events),
        "last_timestamp": events[0].get("timestamp"),
        "by_handler": by_handler,
    }


def ensure_codex_hooks_enabled() -> dict:
    """
    Make sure Codex will load both user-level and plugin-bundled hooks.

    Writes `plugin_hooks = true` (the only flag that actually gates plugin
    hooks). Leaves the canonical `hooks` flag alone since it defaults to true
    and forcing it would just create churn for users who deliberately turned it
    off.
    """
    config_path = codex_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    before = codex_hooks_status()
    if before.get("enabled"):
        before["changed"] = False
        return before

    existing = config_path.read_text() if config_path.exists() else ""
    updated = existing
    written_keys: list[str] = []

    if not before.get("user_hooks_enabled"):
        updated = _replace_or_insert_features_flag(updated, "hooks", "true")
        written_keys.append("hooks")

    if not before.get("plugin_hooks_enabled"):
        updated = _replace_or_insert_features_flag(updated, "plugin_hooks", "true")
        written_keys.append("plugin_hooks")

    if updated != existing:
        config_path.write_text(updated)

    status = codex_hooks_status()
    status["changed"] = bool(written_keys)
    status["written_keys"] = written_keys
    if written_keys:
        status["message"] = (
            f"Enabled Codex hook features ({', '.join(written_keys)}) in {config_path}. "
            "Restart Codex so the new feature flags take effect."
        )
    return status
