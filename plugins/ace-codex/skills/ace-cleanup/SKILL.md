---
name: ace-cleanup
description: Use when the user wants to clean up local ACE state under the repo or CODEX_HOME — old session directories, hook event logs, or cached relevance files — without touching the server-side playbook.
---

Invoke directly with `$ace-cleanup`, or ask `@ace-codex` to clean up local ACE state.

Local ACE state lives in two places:
- repo-local: `.codex/.ace-codex/`
- CODEX_HOME fallback: `${CODEX_HOME:-$HOME/.codex}/ace-codex/<workspace-key>/`

Cleanup workflow:
1. Show the user a count of files under each path (`find <path> -type f | wc -l`) so they understand the scope.
2. Identify what to remove. Common targets:
   - sessions older than N days under `sessions/<session_id>/`
   - hook event logs `hook_events.jsonl` (kept for `$ace-doctor` diagnostics)
   - tool use logs `tool_uses.json` from completed sessions
   - relevance logs `relevance.jsonl` from completed sessions
3. Wait for explicit confirmation. Default to `--dry-run` style behavior unless the user opts into a hard delete.
4. Never remove `.codex/ace.json` (the repo binding) or `workspace/domains.json` (live workspace state) unless the user explicitly asks for a full reset.

Backup-first option: run `$ace-export-patterns` if the user worries about losing learning history. Server-side patterns are unaffected.
