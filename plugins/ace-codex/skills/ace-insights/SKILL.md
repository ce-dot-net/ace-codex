---
name: ace-insights
description: Use when the user wants a per-task helpfulness report showing which ACE patterns were injected for past prompts and how relevant they were, rendered as a Markdown summary or HTML report from the local relevance log.
---

Invoke directly with `$ace-insights`, or ask `@ace-codex` for a relevance report.

The PostToolUse and Stop hooks append per-turn relevance entries to `.codex/.ace-codex/sessions/<session_id>/relevance.jsonl` (or the `CODEX_HOME` fallback).

Report workflow:
1. Locate every `relevance.jsonl` under `.codex/.ace-codex/sessions/`.
2. For each turn, gather: prompt (truncated), pattern_count, avg_confidence, domains, tool_count.
3. Render a Markdown table sorted by timestamp (newest first), with columns: turn timestamp, prompt, patterns injected, avg confidence, domains, tools executed.
4. If the user wants HTML, write the same content into `./ace-insights-$(date +%Y%m%d).html` with minimal styling.
5. If no relevance entries exist, point the user at `$ace-status` and suggest running a few real tasks first.

This skill reads only local state and does not call the ACE backend.
