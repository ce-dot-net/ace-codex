# ACE for Codex

ACE turns OpenAI Codex into an agent that **learns from every task**. It searches a per-project playbook before each prompt, injects the most relevant past patterns into the model's context, and feeds every completed turn back into the playbook so the next session is smarter.

This repo packages ACE as a Codex-native marketplace plugin: 21 skills, native lifecycle hooks, an MCP server, and a Python runtime that talks to the real `ace-cli`.

## What you get

- **`<ace-patterns>` injected on every prompt** — relevant snippets from your project's past work, ranked by the ACE backend, capped at 1500 chars
- **Automatic learning at the end of every turn** — the trace ships to ACE; the server analyzes and updates the playbook
- **Domain-shift detection** — when Codex starts touching a new file area mid-turn, ACE re-fetches scoped patterns
- **21 `$ace-*` skills** for setup, search, manual learn, export/import, insights, diagnostics, and more

## Prerequisites

1. **An ACE account** — sign up at <https://ace-ai.app> and create an organization + a project. The plugin binds to one org/project per repo.
2. **`ace-cli`** — the CLI that talks to the ACE backend. Install with:
   ```bash
   npm install -g @ace-sdk/cli
   ```
   The `$ace-install-cli` skill runs the same command from inside Codex if you prefer.
3. **Codex CLI** — version `0.128.0` or newer. Earlier versions miss the plugin-hooks feature gate.

## Install

In Codex, register this repo as a plugin marketplace:

```bash
codex plugin marketplace add ce-dot-net/ace-codex
```

Then in Codex:

1. Open `/plugins`, pick the **CE Dot Net** marketplace, install **ACE Codex**.
2. Quit and relaunch Codex once. Plugin-bundled hooks load at session start, not mid-session.
3. In your project, run `$ace-login` to authenticate `ace-cli` via device-code flow.
4. Run `$ace-configure` to bind this repo to one of your ACE org/project pairs. The skill writes `.codex/ace.json` and adds `[features].plugin_hooks = true` to `~/.codex/config.toml` so plugin hooks actually fire.
5. Quit and relaunch Codex one more time so the new feature flag engages.
6. Optional: run `$ace-bootstrap` to seed the playbook from the codebase. Without bootstrapping, the playbook starts empty and grows as you work.

Verify with `$ace-doctor`. Expect `verdict: ok`.

## Use

After install, just work normally. Every prompt triggers ACE retrieval; every turn end triggers ACE learning. You don't need to invoke any skill manually for the core loop.

When you do want a specific action, ask `@ace-codex` (lets the orchestrator pick the right flow) or invoke a skill directly:

| Skill | Purpose |
|---|---|
| `$ace-login` | Authenticate `ace-cli` via device-code |
| `$ace-configure` | Bind this repo to an ACE org/project |
| `$ace-bootstrap` | Seed the playbook from your codebase |
| `$ace-status` | Auth, config, usage, and review health |
| `$ace-doctor` | Full diagnosis with one-line verdict |
| `$ace-search "query"` | Semantic search across the playbook |
| `$ace-patterns` / `$ace-top` / `$ace-domains` | Browse the playbook |
| `$ace-learn` | Manually capture a learning event |
| `$ace-export-patterns` / `$ace-import-patterns` | Backup / restore the playbook |
| `$ace-insights` | Per-turn relevance report (md / html / json) |
| `$ace-cleanup` | Trim local session state |

Full catalog: [`plugins/ace-codex/README.md`](plugins/ace-codex/README.md#how-to-use-it).

## Where things live

- **Global ACE auth** — `~/.config/ace/config.json` (managed by `ace-cli login`)
- **Per-repo binding** — `<repo>/.codex/ace.json` (org_id, project_id, verbosity)
- **Per-session runtime state** — `<repo>/.codex/.ace-codex/sessions/<session_id>/` (or `${CODEX_HOME}/ace-codex/<workspace-key>/sessions/<session_id>/` if the repo path is read-only)
- **Codex plugin cache** — `~/.codex/plugins/cache/ce-dot-net/ace-codex/<version>/` (managed by Codex)

## Updating

```bash
codex plugin marketplace upgrade ce-dot-net
```

Then quit and relaunch Codex. Codex caches plugins by version; without an upgrade, the old cache stays active even after we ship a new release.

## Troubleshooting in 30 seconds

Run `$ace-doctor`. It prints a one-line `verdict:` that names the most likely failure:

- `SET [features].plugin_hooks = true` → run `$ace-configure`, then restart Codex
- `cached plugin version != repo manifest` → run `codex plugin marketplace upgrade ce-dot-net`, restart
- `plugin not registered` → run `codex plugin marketplace add ce-dot-net/ace-codex` and install in `/plugins`
- `hooks never fired` → fully quit Codex (not resume) and start a fresh thread
- `ok` → you're good

For deeper issues see [`plugins/ace-codex/docs/TROUBLESHOOTING.md`](plugins/ace-codex/docs/TROUBLESHOOTING.md).

## More

- [`plugins/ace-codex/docs/INSTALL.md`](plugins/ace-codex/docs/INSTALL.md) — extended install + configuration walkthrough
- [`plugins/ace-codex/docs/ARCHITECTURE.md`](plugins/ace-codex/docs/ARCHITECTURE.md) — how the plugin maps onto Codex hooks; what ships in each session
- [`plugins/ace-codex/docs/SECURITY.md`](plugins/ace-codex/docs/SECURITY.md) — credentials, network surface, exact trace payload sent to ACE
- [`SUPPORT.md`](SUPPORT.md) — channels for help
- [`PRIVACY.md`](PRIVACY.md) / [`TERMS.md`](TERMS.md) — plugin policies
- [`CHANGELOG.md`](CHANGELOG.md) — release notes

## License

[MIT](LICENSE).
