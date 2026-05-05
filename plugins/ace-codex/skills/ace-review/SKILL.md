---
name: ace-review
description: Use when the user wants the latest ACE review result, wants to inspect whether ACE guidance was helpful, or wants a summary of the last retrieval-learning-review cycle.
---

Invoke directly with `$ace-review`, or ask `@ace-codex` to summarize the latest ACE review state.

This is the Codex-native replacement for the Claude ACE review loop surface.

Read the latest session-scoped ACE state under `.codex/.ace-codex/sessions/<session_id>/`.

If the current session id is available, prefer that exact session directory. Otherwise inspect the most recently updated session directory and read, in order when present:
1. `.codex/.ace-codex/sessions/<session_id>/review_result.json`
2. `.codex/.ace-codex/sessions/<session_id>/review_request.json`
3. `.codex/.ace-codex/sessions/<session_id>/retrieval_state.json`
4. `.codex/.ace-codex/sessions/<session_id>/tool_uses.json`

Report:
- whether a review is pending
- the last helpfulness percentage
- the last recorded time-saved estimate
- the last reason string
- whether the last task accumulated substantial work
