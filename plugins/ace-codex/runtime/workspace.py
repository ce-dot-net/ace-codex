from __future__ import annotations

from pathlib import Path

from config import (
    cached_plugin_versions,
    codex_hooks_status,
    codex_plugin_enabled,
    hook_fire_summary,
    load_binding,
    repo_plugin_manifest_version,
)


def load_workspace_binding(repo_root: Path) -> dict:
    return load_binding(repo_root)


def workspace_is_configured(repo_root: Path) -> bool:
    data = load_workspace_binding(repo_root)
    return bool(data.get("org_id") and data.get("project_id"))


def workspace_diagnostics(repo_root: Path) -> dict:
    binding = load_workspace_binding(repo_root)
    cached = cached_plugin_versions()
    repo_version = repo_plugin_manifest_version(repo_root)
    cached_versions = sorted({entry.get("version") for entry in cached if entry.get("version")})
    drift = bool(repo_version and cached_versions and repo_version not in cached_versions)
    return {
        "binding": binding,
        "configured": bool(binding.get("org_id") and binding.get("project_id")),
        "hooks": codex_hooks_status(),
        "plugin": {
            "repo_version": repo_version,
            "cached_versions": cached_versions,
            "cache_entries": cached,
            "version_drift": drift,
            "enablement": codex_plugin_enabled(),
        },
        "hook_fires": hook_fire_summary(repo_root),
    }
