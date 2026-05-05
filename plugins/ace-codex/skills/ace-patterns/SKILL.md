---
name: ace-patterns
description: Use when the user wants to browse the ACE playbook contents organized by section (strategies, snippets, troubleshooting, apis), or filter patterns by minimum helpful score.
---

Invoke directly with `$ace-patterns`, or ask `@ace-codex` to show the playbook contents.

Run `ace-cli patterns`. Useful flags:
- `--section <strategies|snippets|troubleshooting|apis>` to filter by section
- `--min-helpful <n>` to hide low-value patterns
- `--json` for machine output

If the user wants the highest-scored patterns rather than the full listing, use `$ace-top` instead.
