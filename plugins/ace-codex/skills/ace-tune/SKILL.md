---
name: ace-tune
description: Use when the user wants to adjust ACE server-side tuning knobs for the current project — for example retrieval thresholds, top-k limits, or other constitution settings — without leaving the Codex session.
---

Invoke directly with `$ace-tune`, or ask `@ace-codex` to tune ACE settings.

Run `ace-cli tune` for the interactive flow. Common non-interactive flags:
- `--constitution-threshold <0.0-1.0>` — retrieval similarity threshold
- `--scope <project>` — apply at the project scope (default)

Confirm changes with the user before applying. After tuning, run `$ace-status` so the new effective settings are visible.
