# Install ACE Codex

The short version is in the [repo README](../../../README.md#install). This document is the long-form walkthrough with all the moving pieces explained.

## 1. Create an ACE account

The plugin talks to the ACE backend at <https://ace-ai.app>. Before installing anything locally:

1. Sign up at <https://ace-ai.app>.
2. Create an organization, then a project inside that organization. The plugin binds one repo to one org/project pair.
3. Note the `org_id` (starts with `org_`) and `project_id` (starts with `prj_`). You'll see them in the dashboard. The plugin discovers them automatically once you log in via `ace-cli`, but having them handy helps with manual fallback.

You can also create the project later from the dashboard while bound to a different one — the binding lives in `.codex/ace.json` per repo, so each project you open in Codex picks its own.

## 2. Install `ace-cli`

```bash
npm install -g @ace-sdk/cli
ace-cli --version
```

Or use the `$ace-install-cli` skill once the plugin is installed in step 3 — it does the same `npm install` and verifies the version.

## 3. Add this repo as a Codex marketplace

```bash
codex plugin marketplace add ce-dot-net/ace-codex
```

This is the published path. For local development from a clone, the equivalent is:

```bash
git clone git@github.com:ce-dot-net/ace-codex.git
cd ace-codex
codex plugin marketplace add .
```

Codex stores the marketplace registration under `[marketplaces.ce-dot-net]` in `~/.codex/config.toml` and downloads the plugin into `~/.codex/plugins/cache/ce-dot-net/ace-codex/<version>/`.

## 4. Install the plugin from the marketplace

In Codex:

1. Open `/plugins`.
2. Pick the **CE Dot Net** marketplace.
3. Install **ACE Codex**.
4. **Quit and relaunch Codex.** Plugin-bundled hooks load at session start.

The plugin is Codex-native. It does not use Claude-style slash commands, so don't look for `/ace-*` — use `$ace-*` (skill invocation) or `@ace-codex` (orchestrator routing).

## 5. Authenticate `ace-cli`

Inside Codex, run `$ace-login`. The skill walks you through the device-code flow:

1. `ace-cli` prints a verification URL and a 6-character code.
2. Open the URL in your browser, paste the code, approve.
3. The CLI polls until authorized and stores tokens at `~/.config/ace/config.json`.

If you already authenticated outside Codex, the skill notices and skips ahead.

## 6. Bind the repo to an ACE org/project

Run `$ace-configure`. The skill:

1. Verifies `ace-cli whoami --json` returns authenticated.
2. Fetches a fresh org list with `ace-cli orgs --json`. You pick one.
3. Fetches a fresh project list with `ace-cli projects --org <id> --json`. You pick one.
4. Saves the binding to `.codex/ace.json`:

   ```json
   {
     "org_id": "org_xxx",
     "project_id": "prj_xxx",
     "verbosity": "detailed"
   }
   ```

5. Adds `[features].plugin_hooks = true` to `~/.codex/config.toml` so plugin-bundled hooks fire. Without this, the rest of the plugin is silently inert. The canonical `hooks` flag (alias `codex_hooks`) is on by default and only governs `~/.codex/hooks.json` — plugin-bundled hooks are gated separately.

After this step, **quit and relaunch Codex one more time.** Feature flags engage at session start.

### Manual fallback if the picker fails

The same flow can be done by hand. Discovery helpers:

```bash
./plugins/ace-codex/scripts/ace-orgs.sh
ACE_ORG_ID=<org_id> ./plugins/ace-codex/scripts/ace-projects.sh
ACE_ORG_ID=<org_id> ACE_PROJECT_ID=<project_id> ./plugins/ace-codex/scripts/ace-configure.sh
```

If discovery still fails, copy `plugins/ace-codex/docs/ace.example.json` to `.codex/ace.json` and fill in the IDs by hand.

## 7. (Optional) Seed the playbook

```text
$ace-bootstrap
```

This runs `ace-cli bootstrap --json --mode hybrid --thoroughness medium` against the current repo. The ACE backend extracts patterns from your docs, recent git history, and source files. Without bootstrapping the playbook starts empty and grows as you work.

## 8. Verify

```text
$ace-doctor
```

Expect a final line `verdict: ok`. If you see anything else, the verdict tells you what to fix; deeper coverage is in [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## Where state lives

| Path | Purpose |
|---|---|
| `~/.config/ace/config.json` | Global ACE auth (managed by `ace-cli`) |
| `~/.codex/config.toml` | Codex config — marketplace registration, plugin enable, `[features].plugin_hooks` |
| `~/.codex/plugins/cache/ce-dot-net/ace-codex/<version>/` | Codex's local plugin cache; the running code |
| `<repo>/.codex/ace.json` | Per-repo ACE binding |
| `<repo>/.codex/.ace-codex/sessions/<session_id>/` | Per-session runtime state when the repo path is writable |
| `${CODEX_HOME:-$HOME/.codex}/ace-codex/<workspace-key>/sessions/<session_id>/` | Fallback session state when `<repo>/.codex/` is read-only |
| `<repo>/.codex/.ace-codex/workspace/` | Workspace-scoped state (domain tracking) |
| `${CODEX_HOME:-$HOME/.codex}/ace-codex/<workspace-key>/workspace/` | Fallback workspace state |

Per-session files include `hook_events.jsonl`, `retrieval_state.json`, `tool_uses.json`, `relevance.jsonl`, `learning_result.json`, and `review_request.json`. They are diagnostic; the ACE backend is the source of truth for the playbook itself.

## Optional: `ACE_CLIENT_ID`

If your launcher needs a client tag for ACE analytics, set `ACE_CLIENT_ID` in the launch environment. The plugin does not force a default. Most users never need this.

## Updating

```bash
codex plugin marketplace upgrade ce-dot-net
```

Then **start a new thread** (or relaunch Codex). Codex caches plugins by version directory, so without an upgrade the old cache stays active even after we ship a new release. If `/plugins` does not show an explicit update, reinstall `ace-codex` from the marketplace entry — that forces a re-download.

## Uninstalling

1. In Codex, open `/plugins` and disable / remove **ACE Codex**.
2. Remove the marketplace registration: `codex plugin marketplace remove ce-dot-net`.
3. Optional cleanup of local state: `bash plugins/ace-codex/scripts/ace-cleanup.sh <repo> delete-all`.
4. Optional removal of the binding: `rm <repo>/.codex/ace.json`.

The server-side playbook stays intact unless you run `$ace-clear` first.
