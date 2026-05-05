---
name: ace-clear
description: Use when the user wants to wipe the ACE playbook for the current project, removing all learned patterns. Always confirm with the user before running because the operation is destructive.
---

Invoke directly with `$ace-clear`, or ask `@ace-codex` to reset the ACE playbook.

This is destructive. The playbook is replaced server-side; cached state on the local machine is also reset.

Required confirmation flow:
1. Print which org and project are bound (`.codex/ace.json`).
2. Tell the user the action will permanently delete every learned pattern in that project's playbook.
3. Wait for an explicit confirmation. Do not assume `yes`.
4. Only after explicit confirmation, run `ace-cli clear --yes`.

If the user wants a backup first, run `$ace-export-patterns` and save the JSON before clearing.
