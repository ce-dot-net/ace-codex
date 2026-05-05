# Security model

## What runs locally

ACE Codex executes Python (`hook_entry.py`) and bash wrapper scripts during normal Codex sessions. Both run inside the Codex hook subprocess and share the user's process-level credentials. The plugin does not run any model itself; the Codex agent and `ace-cli` are the only model-aware components.

## Credentials

- ACE auth lives at `~/.config/ace/config.json` and is managed by `ace-cli login`. The plugin never reads or writes this file directly.
- ACE org/project binding for the current repo lives at `<repo>/.codex/ace.json`. The binding is a non-secret pair of identifiers; clearing or sharing it is safe.
- No tokens are written into `<repo>/.codex/.ace-codex/` state. Hook event logs, tool traces, and relevance entries are organization data (filenames, prompt prefixes, tool inputs) but contain no auth material.

## Network

- The plugin makes outbound calls only via `ace-cli`, which talks to the configured ACE backend.
- `ace-cli search`, `ace-cli learn`, `ace-cli whoami`, `ace-cli status`, `ace-cli orgs`, and `ace-cli projects` are the only commands the runtime ever invokes from inside hooks.
- Other `ace-cli` commands (export/import/delta/clear/tune/insights/etc.) only run when the user explicitly invokes the corresponding `$ace-*` skill.

## Permission model

Codex's `PermissionRequest` hook is wired to auto-allow only the `ace-cli` reads and writes the plugin actually needs. The handler matches command prefixes against an allowlist defined in `runtime/ace_codex.py` (`SAFE_PERMISSION_PREFIXES`):

```
ace-cli search
ace-cli cache recall
ace-cli learn
ace-cli whoami
ace-cli status
```

Any other command falls through to Codex's normal approval flow. The plugin does not auto-allow Bash, file edits, or arbitrary commands.

## Sandbox compatibility

The plugin works under Codex's `read-only`, `workspace-write`, and `danger-full-access` sandbox modes. The runtime tolerates a read-only `.codex/` directory by falling back to `${CODEX_HOME:-$HOME/.codex}/ace-codex/<workspace-key>/` for state persistence. Hooks themselves run with the session `cwd` as their working directory.

## What the plugin sends to the ACE backend

The `Stop` hook posts a trajectory to `ace-cli learn --transcript <tempfile>`. The trajectory contains:

- Task description (the user prompt that started the turn, truncated)
- A list of tool calls made during the turn — tool name, tool input, tool response (size-limited)
- The pattern IDs that were injected on UserPromptSubmit
- A truncated final assistant message
- Session and turn identifiers
- Optional git context (commit, branch) auto-detected by `ace-cli`

The temp file is written under the OS temp directory and removed in a `finally` block whether the call succeeds or fails. There is no lingering on-disk copy of the trace.

## What the plugin does NOT send

- Raw transcripts of the entire session
- File contents that were read but not modified
- Environment variables beyond `ACE_ORG_ID`, `ACE_PROJECT_ID`, `ACE_VERBOSITY`, `ACE_CLIENT_ID`
- Any file under `~/.codex/` outside the binding-derived org/project context

## Reset paths

- `$ace-cleanup` removes local session state without touching the server playbook or the `.codex/ace.json` binding.
- `$ace-clear` resets the server-side playbook (destructive; prompts for confirmation).
- Removing the plugin via Codex plugin management leaves `.codex/ace.json` and `.codex/.ace-codex/` in place; delete them manually if a clean uninstall is required.

## Known limitations

- Codex `PermissionRequest` hook responses for `permissionDecision: "allow"` and `"ask"` are parsed but unimplemented as of `rust-v0.128.0` and "fail open" — meaning auto-allow behavior may change in a future Codex release. The plugin's intent is conservative (only `ace-cli` reads), but Codex's enforcement of that intent is upstream.
- Plugins cannot ship arbitrary `[permissions.<name>]` profiles or `default_permissions` defaults. Recommended user-level permission profiles are in `INSTALL.md`.
