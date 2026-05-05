# Architecture

## Overview

ACE Codex is a Codex-native plugin that ports the Claude ACE plugin's retrieval-and-learning loop onto Codex's six lifecycle hooks. The plugin owns no models or LLM logic itself — every retrieval, learning, and pattern operation is delegated to a separate `ace-cli` (Node) process that talks to the ACE backend.

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│ Codex turn  │ →   │ hook_entry.py    │ →   │ ace-cli       │
│ (TUI)       │     │ (per-event)      │     │ (Node, REST)  │
└─────────────┘     └──────────────────┘     └───────────────┘
        │                  │                          │
        │                  │                          ▼
        │                  │                  ┌───────────────┐
        │                  │                  │ ACE backend   │
        │                  │                  │ (server side) │
        │                  │                  └───────────────┘
        │                  ▼
        │           .codex/.ace-codex/      (per-session state)
        │                ├─ sessions/<sid>/
        │                │   ├─ hook_events.jsonl
        │                │   ├─ retrieval_state.json
        │                │   ├─ tool_uses.json
        │                │   ├─ relevance.jsonl
        │                │   ├─ learning_result.json
        │                │   └─ review_request.json
        │                └─ workspace/
        │                    └─ domains.json
        │
        ▼
   `<ace-patterns>` injected into next turn
```

## Three roles

The ACE methodology distinguishes Generator, Reflector, and Curator. In this Codex port:

- **Generator** is Codex itself. The plugin injects retrieved patterns as `additionalContext` on `UserPromptSubmit` so Codex sees them before generating.
- **Reflector** is the `Stop` hook plus the `ace-cli learn` call. Each turn's trajectory is collected from `PostToolUse` events into `tool_uses.json`, then submitted on `Stop`.
- **Curator** is the ACE backend. Server-side analysis decides which trace fragments become persistent playbook patterns; the plugin only ships traces.

## Lifecycle mapping

| Codex hook | Handler in `hook_entry.py` | Effect |
|---|---|---|
| `SessionStart` | `handle_session_start` | Restore prior retrieval state on resume; inject `review_request` if a previous turn left one |
| `UserPromptSubmit` | `handle_user_prompt_submit` | Run `ace-cli search`; persist `retrieval_state.json`; inject `<ace-patterns>` context; refuse retrieval-required prompts when ACE is unconfigured or unauthenticated |
| `PreToolUse` (Bash, apply_patch) | `handle_pre_tool_use` | Block state-changing tools when retrieval is pending; otherwise allow |
| `PostToolUse` (Bash, apply_patch, etc.) | `handle_post_tool_use` | Append to `tool_uses.json`; extract file path from `tool_input.command`; detect domain shift; trigger scoped re-search when needed |
| `PermissionRequest` | `handle_permission_request` | Auto-allow safe `ace-cli` calls (search, learn, status, whoami, cache recall) |
| `Stop` | `handle_stop` | Build trace from `tool_uses.json` + `retrieval_state.json`; call `ace-cli learn --transcript`; write `review_request.json` for the next session start |

## State directories

State lives under `.codex/.ace-codex/` when the repo is writable, otherwise under `${CODEX_HOME:-$HOME/.codex}/ace-codex/<workspace-key>/` where `<workspace-key>` is the first 12 hex chars of the SHA-1 of the resolved repo path. The fallback keeps end-user installs working when the project's `.codex/` directory is read-only.

Per-session files:
- `hook_events.jsonl` — every hook fire is appended here for `$ace-doctor` audit
- `retrieval_state.json` — last UserPromptSubmit search result + pattern IDs
- `tool_uses.json` — accumulated tool calls for the current turn
- `relevance.jsonl` — per-turn relevance summary consumed by `$ace-insights`
- `learning_result.json` — output of the most recent `ace-cli learn`
- `review_request.json` — prompt to inject on the next `SessionStart`

Workspace-scoped files:
- `workspace/domains.json` — known domains + last-touched domain for shift detection

## ace-cli transport

The plugin shells out to `ace-cli` for every backend operation. Two choices matter:

1. **`learn` uses `--transcript <tempfile>`, not `--stdin`.** Codex's nested hook subprocess context (`/bin/sh -lc` → `python3 hook_entry.py` → `subprocess.run(input=…)`) reproducibly trips a Node-side "Failed to read from stdin" error. Writing the trace to a temp file under `tempfile.gettempdir()` and pointing `--transcript` at it bypasses the Node TTY/pipe race entirely.
2. **`search` keeps `--stdin`.** Query payloads are short and the same race does not trigger reliably; `--stdin` keeps the pipeline simple.

Both binding (`org_id`, `project_id`, `verbosity`) and `ACE_CLIENT_ID` are passed as environment variables to `ace-cli`, mirroring the auth model used by the standalone CLI.

## Hook command shape

Every entry in `hooks/hooks.json` follows the same dispatcher pattern:

```bash
SCRIPT="${PLUGIN_ROOT:-}/runtime/hook_entry.py"
if [ ! -f "$SCRIPT" ]; then
  for ALT in ./plugins/ace-codex/runtime/hook_entry.py \
    "${CODEX_HOME:-$HOME/.codex}"/plugins/cache/*/ace-codex/*/runtime/hook_entry.py; do
    [ -f "$ALT" ] && SCRIPT="$ALT" && break
  done
fi
[ -f "$SCRIPT" ] && exec python3 "$SCRIPT" <event>
echo '{}'
```

`PLUGIN_ROOT` is set by Codex's hook engine to the installed cache path of this plugin (verified in `codex-rs/hooks/src/engine/discovery.rs:175-180` for `rust-v0.128.0`). The fallback paths cover dev-mode invocation from the repo root and a marketplace-name-agnostic glob over `~/.codex/plugins/cache/*/ace-codex/*` so the same `hooks.json` works whether the plugin is installed under `ce-dot-net` or any other marketplace name.

## Why the hook command emits an empty `{}` on the no-script path

If neither the `PLUGIN_ROOT` script nor any fallback resolves, the hook still must produce valid JSON on stdout for Codex to accept it. `echo '{}'` is the minimal valid `HookSpecificOutput` payload and means "do nothing". Without it, Codex sees an empty stdout for `UserPromptSubmit` (which is parsed as plain text and added as developer context) — harmless but confusing. The empty object keeps the no-op path quiet.

## Why two hook feature flags matter

Codex (v0.128.0) gates plugin-bundled hooks behind `[features].plugin_hooks = true` (`UnderDevelopment`, default `false`) — separate from `[features].hooks` / `codex_hooks` (Stable, default `true`) which only governs `~/.codex/hooks.json` and `<repo>/.codex/hooks.json`. The plugin's `hooks/hooks.json` is silently ignored unless `plugin_hooks` is set explicitly. `$ace-configure` writes the flag automatically; `$ace-doctor` reports its state and the most likely silent failure cause.
