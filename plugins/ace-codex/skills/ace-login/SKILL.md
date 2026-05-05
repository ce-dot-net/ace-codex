---
name: ace-login
description: Use when the user wants to log into ACE, verify ace-cli authentication, or set up device-code login for ace-cli.
---

Invoke directly with `$ace-login`, or ask `@ace-codex` to handle ACE login for this workspace.

Check `ace-cli` first. If missing, tell the user to install `@ace-sdk/cli`.

Preferred flow:
1. Run `ace-cli whoami --json`.
2. If authenticated, report current account and stop.
3. If unauthenticated, run `ace-cli login --no-browser`.
4. Explain the verification URL and device code shown by the CLI.
5. Re-run `ace-cli whoami --json` to verify success.
6. Suggest `ace-configure` next if the workspace is not bound to an ACE project.

Project-local configuration does not live in `.claude/settings.json`. For Codex, use `.codex/ace.json`.
If the launcher needs a client tag for analytics, pass `ACE_CLIENT_ID` in the launch environment; do not persist client identity in repo config.
