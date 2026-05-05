# Install ACE Codex

## 1. Open the repository in Codex

This repo already contains a repo-local marketplace catalog:

```text
.agents/plugins/marketplace.json
```

## 2. Install the plugin from the repo marketplace

Use Codex plugin management to install:

- `ace-codex`

The release version for the plugin is defined in `plugins/ace-codex/.codex-plugin/plugin.json`.

ACE Codex is Codex-native. It does not use Claude-style slash commands.

If you are updating an existing install, reinstall `ace-codex` from Codex plugin management when a new plugin version is published.

## 3. Install and authenticate `ace-cli`

```bash
npm install -g @ace-sdk/cli
ace-cli login --no-browser
```

## 4. Bind this repo to an ACE org/project

Create:

```text
.codex/ace.json
```

You can start from:

```text
plugins/ace-codex/docs/ace.example.json
```

Example:

```json
{
  "org_id": "org_xxx",
  "project_id": "prj_xxx",
  "verbosity": "detailed"
}
```

Helper discovery commands from repo root:

```bash
./plugins/ace-codex/scripts/ace-orgs.sh
ACE_ORG_ID=<org_id> ./plugins/ace-codex/scripts/ace-projects.sh
ACE_ORG_ID=<org_id> ACE_PROJECT_ID=<project_id> ./plugins/ace-codex/scripts/ace-configure.sh
```

If project discovery still fails, use the known ACE project ID manually and write `.codex/ace.json` directly from the example file.

`ace-configure` also enables Codex plugin-bundled hooks in `~/.codex/config.toml` by ensuring:

```toml
[features]
plugin_hooks = true
```

Why this flag matters:
- Codex distinguishes two hook features. `hooks` (alias `codex_hooks`) is Stable and on by default — it loads `~/.codex/hooks.json` and `<repo>/.codex/hooks.json`.
- `plugin_hooks` is "Under Development" and **off by default**. Without it, the ACE plugin's bundled `hooks/hooks.json` is silently ignored even though the plugin is installed and enabled. This is the most common reason ACE retrieval and learning never fire.

After enabling the flag, **restart Codex** so the change takes effect.

## 5. Use the plugin

Use `@ace-codex` when you want the plugin to route you to the right ACE workflow.

Use direct skills when you already know the task:

- setup: `$ace-login`, `$ace-configure`
- initialization: `$ace-bootstrap`
- health: `$ace-status`
- diagnostics: `$ace-doctor`
- review: `$ace-review`

If your Codex launcher needs a client tag for ACE analytics, set `ACE_CLIENT_ID` in the launch environment. The plugin does not force a default client id.

If your Codex session cannot write into the repo-local `.codex` directory, ACE runtime state falls back to `CODEX_HOME/ace-codex/<workspace-key>/`. You do not need to configure that path manually.

After install, reinstall, or `ace-configure`, start a new thread. Restart Codex if the current session does not pick up the updated plugin or hook state.
