# ACE Codex Marketplace

Public repo for the `ace-codex` Codex plugin and its repo-local marketplace source.

## Quickstart

1. Clone the repo:

   ```bash
   git clone git@github.com:ce-dot-net/ace-codex.git
   ```

2. Add the repository as a Codex marketplace:

   ```bash
   codex plugin marketplace add .
   ```

3. Open Codex plugin management and install `ace-codex` from this marketplace.
4. Install and authenticate `ace-cli` if it is not already present.
5. Run `$ace-configure` once to bind the workspace with a real ACE org/project in `.codex/ace.json` and enable `[features].plugin_hooks = true` (the experimental flag that gates plugin-bundled hooks; `codex_hooks` alone is not enough).
6. Use `@ace-codex` for general ACE help, or invoke a specific skill like `$ace-login`, `$ace-configure`, `$ace-bootstrap`, or `$ace-status`.
7. If the repo-local `.codex` directory is not writable in your Codex session, ACE runtime state automatically falls back to `CODEX_HOME/ace-codex/<workspace-key>/`.
8. Start a new thread after install or configure so Codex loads the current plugin and hook state.

ACE Codex is Codex-native. It does not use Claude-style slash commands.

## What the plugin provides

- 21 Codex skills covering setup, retrieval, learning, playbook management, diagnostics, and reporting (full catalog in [`plugins/ace-codex/README.md`](plugins/ace-codex/README.md#how-to-use-it))
- Six lifecycle hooks for prompt-time retrieval, tool accumulation, domain-shift re-search, review injection, and per-turn learning
- A bundled MCP server (`ace-pattern-learning`) via `@ce-dot-net/ace-client`
- Python runtime helpers that call the real `ace-cli`
- Two invocation patterns: `@ace-codex` for routing and `$ace-*` for direct skill use

## Repository layout

- `.agents/plugins/marketplace.json`: repo-local Codex marketplace catalog
- `plugins/ace-codex/`: the Codex plugin bundle (skills, hooks, runtime, scripts, MCP)
- `plugins/ace-codex/docs/ARCHITECTURE.md`: role mapping, lifecycle, state layout, transport rationale
- `plugins/ace-codex/docs/SECURITY.md`: credentials, network surface, permission allowlist, trace schema
- `plugins/ace-codex/docs/TROUBLESHOOTING.md`: verdict-by-verdict remediation
- `plugins/ace-codex/docs/INSTALL.md`: install flow including the `plugin_hooks` feature flag
- `plugins/ace-codex/docs/VERSIONING.md`: versioning policy
- `plugins/ace-codex/docs/ace.example.json`: public example binding template
- `CHANGELOG.md`: release notes
- `PRIVACY.md`: plugin privacy policy
- `TERMS.md`: plugin terms of use
- `LICENSE`: repository license
- `SUPPORT.md`: install and runtime support

## Configuration

- Global ACE auth and identity live in `~/.config/ace/config.json`
- Repo-local ACE workspace binding lives in `.codex/ace.json`
- Session-scoped ACE runtime state lives in `.codex/.ace-codex/sessions/<session_id>/` when writable, otherwise `CODEX_HOME/ace-codex/<workspace-key>/sessions/<session_id>/`
- Workspace-scoped domain state lives in `.codex/.ace-codex/workspace/` when writable, otherwise `CODEX_HOME/ace-codex/<workspace-key>/workspace/`
- Codex plugin-hook enablement lives in `~/.codex/config.toml` under `[features]` with `plugin_hooks = true` (the canonical `hooks` flag is on by default for user-level hooks; plugin-bundled hooks need the separate `plugin_hooks` flag)
- `ACE_CLIENT_ID` is optional and may be set by the launcher if needed

Example binding template:

- `plugins/ace-codex/docs/ace.example.json`

## Release policy

The plugin version is defined in `plugins/ace-codex/.codex-plugin/plugin.json` and follows semver.

- bump `patch` for docs or release hygiene
- bump `minor` for backwards-compatible workflow additions
- bump `major` for breaking manifest or hook changes

See [`plugins/ace-codex/docs/VERSIONING.md`](plugins/ace-codex/docs/VERSIONING.md) and [`CHANGELOG.md`](CHANGELOG.md).

## Updates

- Bump the plugin version for every release so Codex can resolve a new cached bundle.
- End users update through Codex plugin management.
- If Codex does not show an explicit update action for `ace-codex`, reinstall the plugin from the marketplace entry.
- After reinstalling or toggling the plugin, start a new thread. Restart Codex if the current session does not pick up the change.

### Why hooks may appear silent

The most common cause is that Codex has two separate hook feature flags and only one of them is on by default:

| Flag | Stage | Default | Loads |
|---|---|---|---|
| `[features].hooks` (alias `codex_hooks`) | Stable | **ON** | `~/.codex/hooks.json` and `<repo>/.codex/hooks.json` |
| `[features].plugin_hooks` | UnderDevelopment | **OFF** | Plugin-bundled `hooks/hooks.json` (which is what ACE Codex uses) |

If `$ace-doctor` reports that hooks have never fired, walk through these in order:

1. `[features].plugin_hooks = true` must be present in `~/.codex/config.toml`. Run `$ace-configure` to set it, then **restart Codex** so the experimental flag actually engages. Setting only `codex_hooks = true` is **not enough** — that alias toggles the user-level loader, not the plugin loader.
2. `[plugins."ace-codex@<marketplace>"] enabled = true` must be present. Open the Codex plugin directory and confirm `ace-codex` is enabled.
3. The cached version under `~/.codex/plugins/cache/<marketplace>/ace-codex/<version>/` must match the repo manifest version. If they drift, run:

   ```bash
   codex plugin marketplace upgrade <marketplace>
   ```

   then start a new thread.
4. The current project must be **trusted** for repo-local config layers to load. Codex prompts on first session; you can also confirm via `[projects."<repo path>"] trust_level = "trusted"` in `~/.codex/config.toml`. Plugin-bundled hooks themselves do not require project trust, but `<repo>/.codex/ace.json` binding does.
5. After any of the above changes, **start a new thread**. Codex loads plugins and hook config at session start, not mid-session.

Run `$ace-doctor` to print a one-line `verdict:` that names the likely cause.

## Validation

- Unit and script-mock coverage runs in `pytest`.
- Hook entrypoints are exercised through CLI-style JSON payload tests that simulate native Codex hook events.
- Marketplace registration is verified in an isolated `HOME` by running `codex plugin marketplace add .` and asserting the resulting `~/.codex/config.toml`.

## Support

See [`SUPPORT.md`](SUPPORT.md) for install and runtime troubleshooting.
