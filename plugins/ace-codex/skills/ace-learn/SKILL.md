---
name: ace-learn
description: Use when the user wants to manually submit a learning event to ACE — for example to capture a finding from outside the automatic Stop-hook flow, or to attach a specific task description to the current trajectory.
---

Invoke directly with `$ace-learn`, or ask `@ace-codex` to submit a learning event.

The Stop hook already submits learning events automatically after every turn. Use this skill only when the user wants to manually capture a learning event.

Use `--transcript <file>` rather than `--stdin` when invoked from a Codex hook context, because nested subprocess stdin is unreliable. For interactive use, the simplest form is:

```bash
ace-cli learn --task "<short task description>" --success --output "<one-paragraph summary>"
```

For a structured trace from a file:

```bash
ace-cli learn --transcript /path/to/trace.json --verbosity detailed
```

Useful flags:
- `--success` / `--failure`
- `--task <description>`
- `--output <text>` for a free-text summary
- `--git-commit <hash>` / `--git-branch <name>` to override auto-detection
- `--no-stream` for sync POST instead of streaming
- `--timeout <ms>` (default 60000)
