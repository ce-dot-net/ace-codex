---
name: ace-configure
description: Use when the user wants to bind the current workspace to an ACE organization and project after logging in with ace-cli.
---

Invoke directly with `$ace-configure`, or ask `@ace-codex` to configure this workspace for ACE.

This workflow requires prior authentication.

Preferred flow:
1. Verify auth with `ace-cli whoami --json`.
2. Fetch fresh organizations with `ace-cli orgs --json`.
3. Fetch fresh projects with `ace-cli projects list --org <org_id> --json`.
4. Save the selected `org_id`, `project_id`, and verbosity into `.codex/ace.json`.
5. Keep global auth in `~/.config/ace/config.json`; do not copy tokens into the repo.
6. Ensure `[features].plugin_hooks = true` is present in `~/.codex/config.toml`. Plugin-bundled hooks are gated behind this UnderDevelopment flag (default OFF). The deprecated `codex_hooks` alias only toggles the user-level hook loader; plugin-bundled hooks need `plugin_hooks` explicitly.
7. Remind the user to **restart Codex** after the feature flag is written so the change takes effect.
8. Tell the user that ACE runtime state uses repo-local `.codex/.ace-codex/` when writable and falls back to `CODEX_HOME/ace-codex/<workspace-key>/` automatically when the repo path is not writable.

When asked what this command changes, say:
- global identity stays in `~/.config/ace/config.json`
- repo binding lives in `.codex/ace.json`
- `[features].plugin_hooks = true` is added to `~/.codex/config.toml` if missing

If project discovery fails, surface the raw ACE backend error and fall back to manual entry instead of guessing.
Point the user at `plugins/ace-codex/docs/ace.example.json` for the manual fallback.
