# ACE Codex Port Backlog

Independent Codex-native backlog for the `ace-codex` marketplace plugin.

## Current status (0.1.18)

- Native marketplace/plugin structure: done
- Codex-native invocation model: done
- Hook runtime hardening: done (`${PLUGIN_ROOT}` env var, `hooks/hooks.json` wrapper, `[features].plugin_hooks = true` flag handling)
- Workspace configure flow: done
- Retrieval/domain-shift detection: done (extracts file paths from `apply_patch` and `Bash` tool inputs since Codex omits `file_path`)
- `ace-cli learn` transport: done (uses `--transcript <tempfile>` to bypass nested-subprocess stdin issues)
- End-to-end live verification: done (UserPromptSubmit, PreToolUse, PostToolUse, Stop all firing in production sessions, ACE patterns retrieved and learned)

## Open work

### 1. Optional marketplace polish

- Add `composerIcon`, `logo`, and `screenshots` under `plugins/ace-codex/assets/` for nicer plugin-directory presentation.

### 2. Continuous compatibility

- Codex hook semantics are still marked Stable for `hooks` and **UnderDevelopment** for `plugin_hooks`. Watch for upstream behavior changes between Codex CLI minor releases.
- The set of supported hook events (6) does not include `Notification`, `SubagentStop`, `SessionEnd`, or `PreCompact`. None are blocking — verified that per-turn `Stop` plus per-subagent child sessions cover the same outcomes.

## Working rules

- Keep this an independent Codex port.
- Prefer Codex-native mechanisms over Claude-style emulation.
- Treat unsupported Claude behaviors as redesign tasks, not copy tasks.
