---
name: ace-orchestrator
description: Use when the user asks generally for ACE help in Codex, wants the right ACE workflow selected automatically, or asks to use the ACE plugin without naming a specific sub-workflow.
---

Invoke this flow with `@ace-codex` when you want routing, or point users to a direct `$ace-*` skill when the task is already known.

Route by intent:
- login/authentication -> `ace-login`
- project binding/configuration -> `ace-configure`
- initial playbook generation -> `ace-bootstrap`
- health/statistics/config debugging -> `ace-status`
- review/helpfulness of prior guidance -> `ace-review`

Do not assume Claude slash commands or `.claude/settings.json`.
Use Codex-native plugin files and `.codex/ace.json`.
