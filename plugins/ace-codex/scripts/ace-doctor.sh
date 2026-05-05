#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
RUNTIME_DIR="$REPO_ROOT/plugins/ace-codex/runtime"

# Allow doctor to run from any cwd by falling back to the installed cache when
# the repo runtime dir is missing (end-user install case).
if [ ! -d "$RUNTIME_DIR" ]; then
    CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
    for CANDIDATE in "$CODEX_HOME_DIR"/plugins/cache/*/ace-codex/*/runtime; do
        if [ -d "$CANDIDATE" ]; then
            RUNTIME_DIR="$CANDIDATE"
            break
        fi
    done
fi

python3 - "$REPO_ROOT" "$RUNTIME_DIR" <<'PY'
from pathlib import Path
import os
import shutil
import sys

repo_root = Path(sys.argv[1])
runtime_dir = Path(sys.argv[2])
sys.path.insert(0, str(runtime_dir))

from ace_cli import orgs, projects, status, whoami
from config import load_binding
from workspace import workspace_diagnostics

print("ACE Doctor")
print(f"repo_root: {repo_root}")
print(f"runtime_dir: {runtime_dir}")
print(f"runtime_dir_exists: {runtime_dir.exists()}")
print(f"python: {sys.executable}")
print(f"ace_cli_on_path: {shutil.which('ace-cli') or '-'}")
print(f"ace_client_id: {os.environ.get('ACE_CLIENT_ID') or '-'}")
print(f"codex_home: {os.environ.get('CODEX_HOME') or str(Path.home() / '.codex')}")

binding = load_binding(repo_root)
diagnostics = workspace_diagnostics(repo_root)
hooks = diagnostics.get("hooks", {})
plugin = diagnostics.get("plugin", {})
fires = diagnostics.get("hook_fires", {})

print(f"binding_present: {bool(binding)}")
if binding:
    print(f"binding_org_id: {binding.get('org_id', '-')}")
    print(f"binding_project_id: {binding.get('project_id', '-')}")
    print(f"binding_verbosity: {binding.get('verbosity', '-')}")

print(f"codex_hooks_enabled: {hooks.get('enabled', False)}")
print(f"codex_hooks_status: {hooks.get('status', '-')}")
print(f"codex_user_hooks_flag: {hooks.get('user_hooks_enabled', False)}")
print(f"codex_plugin_hooks_flag: {hooks.get('plugin_hooks_enabled', False)}")
print(f"codex_hooks_config_path: {hooks.get('config_path', '-')}")
print(f"codex_hooks_message: {hooks.get('message', '-')}")

print(f"plugin_repo_version: {plugin.get('repo_version') or '-'}")
print(f"plugin_cached_versions: {','.join(plugin.get('cached_versions', [])) or '-'}")
print(f"plugin_version_drift: {plugin.get('version_drift', False)}")
enablement = plugin.get("enablement", {})
print(f"plugin_enabled_in_codex: {enablement.get('any_enabled', False)}")
print(f"plugin_config_keys: {','.join(item['key'] for item in enablement.get('entries', [])) or '-'}")

print(f"hook_event_count_recent: {fires.get('event_count', 0)}")
print(f"hook_last_timestamp: {fires.get('last_timestamp') or '-'}")
by_handler = fires.get("by_handler", {})
if by_handler:
    print(f"hook_handlers_seen: {','.join(f'{k}={v}' for k, v in sorted(by_handler.items()))}")
else:
    print("hook_handlers_seen: -")

# Verdict: surface the most likely cause of silent hook failure.
if not hooks.get("user_hooks_enabled", False):
    print("verdict: user-level hooks disabled. Remove [features].hooks = false / codex_hooks = false and restart Codex.")
elif not hooks.get("plugin_hooks_enabled", False):
    print("verdict: SET [features].plugin_hooks = true in ~/.codex/config.toml and restart Codex. Plugin-bundled hooks are gated behind this flag (codex_hooks alone does NOT enable them).")
elif not enablement.get("any_match"):
    print("verdict: plugin not registered in ~/.codex/config.toml. Run `codex plugin marketplace add` and install ace-codex.")
elif not enablement.get("any_enabled"):
    print("verdict: plugin disabled. Enable ace-codex in the Codex plugin directory.")
elif plugin.get("version_drift"):
    print("verdict: cached plugin version != repo manifest. Run `codex plugin marketplace upgrade` and start a new thread.")
elif fires.get("event_count", 0) == 0:
    print("verdict: hooks never fired. Start a new Codex thread; if still empty, ensure project is trusted and codex was restarted after enabling hooks.")
else:
    print("verdict: ok")

auth = whoami()
print(f"whoami_ok: {auth.ok}")
if auth.data:
    print(f"authenticated: {auth.data.get('authenticated', False)}")
    print(f"token_status: {auth.data.get('token_status', '-')}")
    print(f"current_org_id: {auth.data.get('current_org_id', '-')}")
else:
    print(auth.stderr.strip() or auth.stdout.strip() or "whoami returned no structured data")

org_result = orgs()
print(f"orgs_ok: {org_result.ok}")
if org_result.data:
    print(f"org_count: {org_result.data.get('count', 0)}")
else:
    print(org_result.stderr.strip() or org_result.stdout.strip() or "org lookup returned no structured data")

org_id = binding.get("org_id") if binding else None
if org_id:
    prj = projects(org_id)
    print(f"projects_ok: {prj.ok}")
    if prj.data:
        projects_list = prj.data.get("projects", [])
        print(f"projects_count: {len(projects_list)}")
    else:
        print(prj.stderr.strip() or prj.stdout.strip() or "project lookup returned no structured data")

if binding:
    st = status(binding)
    print(f"status_ok: {st.ok}")
    if not st.data:
        print(st.stderr.strip() or st.stdout.strip() or "status returned no structured data")
PY
