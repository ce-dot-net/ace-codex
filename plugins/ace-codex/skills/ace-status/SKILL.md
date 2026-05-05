---
name: ace-status
description: Use when the user wants ACE health, playbook statistics, auth state, or next-step remediation for ace-cli in this workspace.
---

Invoke directly with `$ace-status`, or ask `@ace-codex` to check ACE health for this workspace.

Status flow:
1. Check `ace-cli`.
2. Check authentication with `ace-cli whoami --json`.
3. If unauthenticated, recommend `ace-login`.
4. If authenticated, run `./plugins/ace-codex/scripts/ace-status.sh`.
5. Also inspect workspace-local `.codex/ace.json` and local ACE Codex state files when present.
6. If you need the raw CLI, pass `--org` and `--project` from `.codex/ace.json`; do not call `ace-cli status --json` without them in non-interactive mode.

Report:
- auth state
- bound org/project
- playbook counts
- recent review result if available
- backend failure details if `ace-cli status` cannot resolve the project
