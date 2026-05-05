---
name: ace-bootstrap
description: Use when the user wants to populate an ACE playbook from docs, git history, or local files using ace-cli bootstrap.
---

Invoke directly with `$ace-bootstrap`, or ask `@ace-codex` to bootstrap the ACE playbook for this workspace.

Run `ace-cli bootstrap` for the current repository after confirming the workspace is configured.

Default recommendation:
- `--mode hybrid`
- `--thoroughness medium`

After bootstrap:
1. Summarize the result.
2. Run `ace-cli status --json` if needed.
3. Tell the user whether patterns were created or merged.
