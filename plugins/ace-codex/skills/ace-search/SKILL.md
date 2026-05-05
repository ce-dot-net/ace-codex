---
name: ace-search
description: Use when the user wants to manually run a semantic search against the ACE playbook for a natural-language query, optionally scoped to specific domains or sections, without going through the automatic UserPromptSubmit retrieval path.
---

Invoke directly with `$ace-search`, or ask `@ace-codex` to search the ACE playbook.

Run `ace-cli search "<query>"`. Useful flags:
- `--top-k <n>` to bound results (1-100)
- `--section <strategies|snippets|troubleshooting|apis>` to filter
- `--allowed-domains <a,b>` to whitelist domains
- `--blocked-domains <a,b>` to exclude domains
- `--threshold <0.0-1.0>` to override the server similarity threshold
- `--json` for machine output

The repo binding in `.codex/ace.json` provides org/project automatically. If the binding is missing, run `$ace-configure` first.
