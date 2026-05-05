---
name: ace-import-patterns
description: Use when the user wants to import a previously exported ACE playbook JSON file into the current project, restoring or seeding patterns from a backup or another project.
---

Invoke directly with `$ace-import-patterns`, or ask `@ace-codex` to restore a playbook.

Run `ace-cli import --file <path>` for a file or `ace-cli import --stdin` to pipe a JSON document. The current project's playbook is updated.

Confirmation flow:
1. Show the org and project bound in `.codex/ace.json`.
2. Tell the user that imported patterns will be merged into that project's playbook.
3. Wait for explicit confirmation before running. Do not assume `yes`.
4. After import, run `$ace-status` so the user sees the new pattern count.
