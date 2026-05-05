---
name: ace-test
description: Use when the user wants a fast self-test that the ACE plugin is properly installed and operational — `ace-cli` reachable, repo binding present, hooks fired recently. Lightweight version of `$ace-doctor` without the full backend probes.
---

Invoke directly with `$ace-test`, or ask `@ace-codex` to verify the plugin is operational.

Run `./plugins/ace-codex/scripts/ace-test.sh` if it exists; otherwise execute these checks inline:

1. `command -v ace-cli` — must succeed.
2. `python3 --version` — required for the hook runtime.
3. `cat .codex/ace.json` — must contain `org_id` and `project_id`.
4. `grep plugin_hooks ~/.codex/config.toml` — must show `plugin_hooks = true` under `[features]`.
5. `find .codex/.ace-codex/sessions -name hook_events.jsonl -newer .codex/ace.json | head -1` — at least one recent file means hooks have fired in this session or a recent one.

Print a single-line `verdict: ok` if all five pass; otherwise print which check failed and refer the user to `$ace-doctor` for deeper diagnosis.
