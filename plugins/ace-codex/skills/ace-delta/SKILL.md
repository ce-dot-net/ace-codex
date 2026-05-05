---
name: ace-delta
description: Use when the user wants to manually add, update, or remove specific patterns in the ACE playbook outside the automatic learning loop — useful for editorial fixes, manual seeding, or pattern maintenance.
---

Invoke directly with `$ace-delta`, or ask `@ace-codex` to apply manual pattern changes.

`ace-cli delta <operation>` accepts `add`, `update`, or `remove` plus a JSON payload of bullets. Provide bullets via one of:
- `--bullets '<json>'` (inline)
- `--file <path>` (file)
- `--stdin` (pipe)

Workflow:
1. Confirm with the user which operation and which patterns are being changed.
2. Construct the bullets JSON. The shape must match the ACE bullet schema; if uncertain, run `$ace-patterns --json` first to inspect existing entries.
3. Apply the change. For destructive `remove` operations, require explicit confirmation just like `$ace-clear`.
4. Run `$ace-status` afterward to confirm the resulting state.
