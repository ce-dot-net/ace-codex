---
name: ace-doctor
description: Use when the user wants to diagnose why ACE is not working in Codex, including hook fire status, plugin version drift, codex_hooks feature flag, CLI auth, repo binding, and ACE backend lookups.
---

Invoke directly with `$ace-doctor`, or ask `@ace-codex` to diagnose the current ACE setup.

Diagnosis order:
1. Confirm `ace-cli` exists on PATH.
2. Confirm `python3` is available.
3. Read `[features].hooks` (or deprecated alias `codex_hooks`) from `~/.codex/config.toml` — this controls the user-level hook loader (default ON).
4. Read `[features].plugin_hooks` from `~/.codex/config.toml` — this controls plugin-bundled hooks (default OFF, "Under Development"). Without this flag, the ACE plugin's `hooks/hooks.json` is silently ignored.
5. Read `[plugins."ace-codex@<marketplace>"]` enablement from `~/.codex/config.toml`.
6. Compare repo manifest version (`plugins/ace-codex/.codex-plugin/plugin.json`) against installed cache versions under `~/.codex/plugins/cache/*/ace-codex/*`.
7. Check hook fire log under `.codex/.ace-codex/sessions/*/hook_events.jsonl` (or the CODEX_HOME fallback).
8. Check `ace-cli whoami --json`.
9. Check `.codex/ace.json` repo binding.
10. Check `ACE_CLIENT_ID` effective value.
11. Check `ace-cli orgs --json`.
12. Check `ace-cli projects list --org <org_id> --json` when org is known.
13. Run `./plugins/ace-codex/scripts/ace-status.sh` when both org and project are configured. For raw output, fall back to `ace-cli status --json --org <org_id> --project <project_id>`.

Print the doctor verdict line. The verdict is one of:
- `verdict: user-level hooks disabled. Remove [features].hooks = false / codex_hooks = false and restart Codex.`
- `verdict: SET [features].plugin_hooks = true in ~/.codex/config.toml and restart Codex. Plugin-bundled hooks are gated behind this flag (codex_hooks alone does NOT enable them).`
- `verdict: plugin not registered in ~/.codex/config.toml. Run codex plugin marketplace add ...`
- `verdict: plugin disabled. Enable ace-codex in the Codex plugin directory.`
- `verdict: cached plugin version != repo manifest. Run codex plugin marketplace upgrade ...`
- `verdict: hooks never fired. Start a new Codex thread; if still empty, ensure project is trusted and codex was restarted.`
- `verdict: ok`

When a command fails, show the exact stderr/stdout summary and identify whether the failure is:
- local CLI missing
- python3 missing
- user-level hooks feature flag off (`hooks = false`)
- plugin-bundled hooks feature flag off (`plugin_hooks` missing — this is the most common silent failure)
- plugin not installed or disabled
- plugin cache stale (version drift)
- hooks never fired (project untrusted, codex not restarted, or new thread not started)
- auth missing
- repo config missing
- client env missing or wrong
- ACE backend failure
