# ACE Codex

Codex-native ACE plugin for setup, bootstrap, review, and workspace health.

## What it contains

- 21 skills covering setup, retrieval, learning, playbook management, diagnostics, and reporting
- Six lifecycle hooks (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `Stop`) for automatic retrieval, tool accumulation, domain-shift re-search, review injection, and per-turn learning
- A bundled MCP server (`ace-pattern-learning` via `@ce-dot-net/ace-client`) for cross-agent pattern access
- Python runtime helpers for ACE state, review parsing, config handling, version drift detection, and Codex-native enforcement heuristics

## How to use it

Use `@ace-codex` when you want Codex to route you to the right ACE workflow.

Use a direct skill when you already know the job. Codex auto-activates skills by description match, or invoke explicitly with `$skill-name`.

| Skill | What it does |
|---|---|
| `$ace-orchestrator` | Routing entrypoint via `@ace-codex` — picks the right `$ace-*` flow by intent |
| `$ace-login` | Device-code auth flow via `ace-cli login` |
| `$ace-install-cli` | Install or upgrade `ace-cli` from npm |
| `$ace-configure` | Bind the current workspace to an ACE org/project; enable `[features].plugin_hooks = true` |
| `$ace-bootstrap` | Initialize the playbook from docs, git history, and local files |
| `$ace-status` | Auth, config, usage, and review health |
| `$ace-doctor` | Full diagnosis with single-line `verdict:` for the most likely failure |
| `$ace-test` | Lightweight five-check self-test (CLI, python, binding, flag, recent fires) |
| `$ace-review` | Inspect last ACE review result and recent retrieval/learning state |
| `$ace-search` | Manual semantic search against the playbook |
| `$ace-patterns` | Browse the playbook by section |
| `$ace-top` | Highest-rated patterns by helpful score |
| `$ace-domains` | List available pattern domains for filtering |
| `$ace-learn` | Manually submit a learning event |
| `$ace-clear` | Wipe the server-side playbook (destructive; confirms) |
| `$ace-export-patterns` | Back up the playbook to JSON |
| `$ace-import-patterns` | Restore a playbook from JSON |
| `$ace-delta` | Manually add / update / remove specific patterns |
| `$ace-tune` | Adjust ACE server-side tuning (retrieval threshold, etc.) |
| `$ace-cleanup` | Manage local session/relevance state under `.codex/.ace-codex/` |
| `$ace-insights` | Per-turn relevance report (markdown / html / json) from `relevance.jsonl` |

ACE Codex does not expose Claude-style slash commands. It uses Codex mentions, skills, hooks, and `.codex/ace.json`.

## Marketplace layout

- Marketplace catalog: `.agents/plugins/marketplace.json`
- Plugin root: `plugins/ace-codex/`
- Manifest: `plugins/ace-codex/.codex-plugin/plugin.json`

## Install model

This repository is the marketplace source.

- Codex marketplace catalog lives at `.agents/plugins/marketplace.json`
- The plugin entry points at `./plugins/ace-codex`
- Users install the plugin through Codex from the repo-backed marketplace

## Configuration model

This port keeps ACE auth global and project binding local:

- global auth and user identity: `~/.config/ace/config.json`
- repo-local project binding: `.codex/ace.json`
- session-scoped ACE runtime state: `.codex/.ace-codex/sessions/<session_id>/` when writable, otherwise `CODEX_HOME/ace-codex/<workspace-key>/sessions/<session_id>/`
- workspace-scoped domain tracking: `.codex/.ace-codex/workspace/` when writable, otherwise `CODEX_HOME/ace-codex/<workspace-key>/workspace/`
- client identifier is optional and can be passed by the launcher via `ACE_CLIENT_ID` if needed

This keeps ACE auth global, uses the Codex-native project file for workspace binding, and leaves client identity to the launch environment.

Example binding template:

- `plugins/ace-codex/docs/ace.example.json`

## Current scope

This v1 is intentionally repo-local and Codex-native:

- If you are migrating from Claude, use `@ace-codex` or `$ace-*` instead of slash commands
- Claude `PreCompact` is not assumed
- Review is modeled as a hook-driven cycle using `UserPromptSubmit` and `Stop`
- Workspace binding uses `.codex/ace.json`

## Further reading

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Generator/Reflector/Curator mapping, hook lifecycle table, state directory layout, ace-cli transport rationale
- [`docs/SECURITY.md`](docs/SECURITY.md) — credentials, network surface, permission auto-allow allowlist, exact trace payload schema
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — verdict-by-verdict remediation matching `$ace-doctor` output
- [`docs/INSTALL.md`](docs/INSTALL.md) — install flow including `[features].plugin_hooks = true` requirement
- [`docs/VERSIONING.md`](docs/VERSIONING.md) — semver policy
