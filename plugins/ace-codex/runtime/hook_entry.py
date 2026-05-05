from __future__ import annotations

import json
import sys
from pathlib import Path

from ace_cli import cache_recall, learn, search, whoami
from ace_codex import (
    build_review_request,
    append_jsonl,
    classify_prompt_for_search,
    detect_domain_shift,
    extract_codex_file_paths,
    hook_events_path,
    latest_session_state_dir,
    load_json,
    now_iso,
    parse_ace_review,
    permission_decision,
    render_patterns_context,
    session_state_dir,
    search_warning_message,
    should_skip_learning,
    workspace_state_dir,
    write_json,
)
from workspace import load_workspace_binding, workspace_is_configured


def _stdin_json() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _repo_root(event: dict) -> Path:
    workspace = event.get("workspace") or {}
    session = event.get("session") or {}
    cwd = (
        event.get("cwd")
        or event.get("workspace_root")
        or event.get("workspaceRoot")
        or event.get("repo_root")
        or event.get("repoRoot")
        or event.get("project_root")
        or event.get("projectRoot")
        or event.get("working_directory")
        or event.get("workingDirectory")
        or workspace.get("root")
        or session.get("cwd")
        or "."
    )
    return Path(cwd).expanduser().resolve()


def _session_id(event: dict) -> str:
    return event.get("session_id") or event.get("turn_id") or "codex-session"


def _session_state_dir(repo_root: Path, event: dict) -> Path:
    return session_state_dir(repo_root, _session_id(event))


def _log_hook_event(repo_root: Path, event: dict, payload: dict) -> None:
    session_id = _session_id(event)
    append_jsonl(
        hook_events_path(repo_root, session_id),
        {
            "hook_event_name": event.get("hook_event_name") or event.get("event") or "unknown",
            "handler": payload.get("handler"),
            "session_id": session_id,
            "turn_id": event.get("turn_id"),
            "transcript_path": event.get("transcript_path"),
            "prompt": (event.get("prompt") or "")[:500],
            "tool_name": event.get("tool_name"),
            "timestamp": now_iso(),
            **payload,
        },
    )


def _log_relevance(repo_root: Path, event: dict, payload: dict) -> None:
    """
    Append a per-turn relevance entry consumed by `$ace-insights`.

    Lives next to `hook_events.jsonl` under the session state dir. Schema:
    `timestamp`, `session_id`, `turn_id`, `prompt`, `pattern_count`,
    `avg_confidence`, `domains`, `tool_count`, `stage`.
    """
    session_id = _session_id(event)
    append_jsonl(
        session_state_dir(repo_root, session_id) / "relevance.jsonl",
        {
            "timestamp": now_iso(),
            "session_id": session_id,
            "turn_id": event.get("turn_id"),
            "prompt": (payload.get("prompt") or event.get("prompt") or "")[:500],
            "pattern_count": payload.get("pattern_count", 0),
            "avg_confidence": payload.get("avg_confidence", 0.0),
            "domains": payload.get("domains") or [],
            "tool_count": payload.get("tool_count", 0),
            "stage": payload.get("stage", ""),
        },
    )


def handle_user_prompt_submit(event: dict) -> dict:
    repo_root = _repo_root(event)
    state_dir = _session_state_dir(repo_root, event)
    workspace_dir = workspace_state_dir(repo_root)
    binding = load_workspace_binding(repo_root)
    prompt = event.get("prompt", "")
    review_request_file = state_dir / "review_request.json"
    _log_hook_event(repo_root, event, {"handler": "user_prompt_submit", "stage": "start"})

    if review_request_file.exists():
        review = load_json(review_request_file, {})
        review_request_file.unlink(missing_ok=True)
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": review.get("prompt", ""),
            }
        }

    if not classify_prompt_for_search(prompt):
        return {}

    if not workspace_is_configured(repo_root):
        _log_hook_event(repo_root, event, {"handler": "user_prompt_submit", "stage": "blocked_unconfigured"})
        return {
            "decision": "block",
            "reason": "ACE workspace not configured. Run ACE configure for this repo before using retrieval-enforced workflows.",
        }

    auth = whoami()
    if not auth.data or not auth.data.get("authenticated", False):
        _log_hook_event(repo_root, event, {"handler": "user_prompt_submit", "stage": "blocked_unauthenticated"})
        return {
            "decision": "block",
            "reason": "ACE is not authenticated. Run ACE login before using retrieval-enforced workflows.",
        }

    session_id = _session_id(event)
    search_result = search(prompt, binding=binding, session_id=session_id)
    patterns = (search_result.data or {}).get("similar_patterns", []) if search_result.data else []
    domains = sorted({p.get("domain") for p in patterns if p.get("domain")})
    retrieval_state = {
        "session_id": session_id,
        "turn_id": event.get("turn_id"),
        "prompt": prompt,
        "needs_search": False,
        "patterns": patterns,
        "pattern_ids": [p.get("id") for p in patterns if p.get("id")],
        "known_domains": domains,
        "last_search_at": now_iso(),
    }
    retrieval_state["transcript_path"] = event.get("transcript_path")
    write_json(state_dir / "retrieval_state.json", retrieval_state)
    write_json(workspace_dir / "domains.json", {"known_domains": domains, "last_domain": None})
    avg_confidence = (
        sum(p.get("confidence", 0) for p in patterns) / len(patterns)
        if patterns
        else 0.0
    )
    _log_hook_event(
        repo_root,
        event,
        {
            "handler": "user_prompt_submit",
            "stage": "searched",
            "pattern_count": len(patterns),
            "domain_count": len(domains),
        },
    )
    _log_relevance(
        repo_root,
        event,
        {
            "stage": "user_prompt_submit",
            "prompt": prompt,
            "pattern_count": len(patterns),
            "avg_confidence": avg_confidence,
            "domains": domains,
        },
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": render_patterns_context(patterns) or search_warning_message(prompt),
        }
    }


def handle_post_tool_use(event: dict) -> dict:
    repo_root = _repo_root(event)
    state_dir = _session_state_dir(repo_root, event)
    workspace_dir = workspace_state_dir(repo_root)
    binding = load_workspace_binding(repo_root)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    tool_response = event.get("tool_response") or {}
    # Codex hook events do not carry a `file_path` field. Derive it from the
    # tool command text so the rest of the domain-shift logic still works.
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        candidates = extract_codex_file_paths(tool_name, tool_input)
        if candidates:
            file_path = candidates[-1]
    tools_file = state_dir / "tool_uses.json"
    tool_uses = load_json(tools_file, [])
    tool_uses.append(
        {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_response": tool_response,
            "file_path": file_path,
            "tool_use_id": event.get("tool_use_id"),
            "turn_id": event.get("turn_id"),
            "session_id": event.get("session_id"),
            "transcript_path": event.get("transcript_path"),
            "timestamp": now_iso(),
        }
    )
    write_json(tools_file, tool_uses)
    _log_hook_event(
        repo_root,
        event,
        {
            "handler": "post_tool_use",
            "stage": "recorded",
            "tool_count": len(tool_uses),
        },
    )

    if not file_path:
        return {}

    domains = load_json(workspace_dir / "domains.json", {"known_domains": [], "last_domain": None})
    shifted = detect_domain_shift(
        file_path,
        domains.get("known_domains", []),
        domains.get("last_domain"),
        last_file_path=domains.get("last_file_path"),
    )
    domains["last_file_path"] = file_path
    if not shifted:
        write_json(workspace_dir / "domains.json", domains)
        return {}

    domains["last_domain"] = shifted
    write_json(workspace_dir / "domains.json", domains)
    filename = Path(file_path).stem
    query = f"{shifted} {filename}".strip()
    search_result = search(query, binding=binding, session_id=None, allowed_domains=[shifted])
    patterns = (search_result.data or {}).get("similar_patterns", []) if search_result.data else []
    _log_hook_event(
        repo_root,
        event,
        {
            "handler": "post_tool_use",
            "stage": "domain_shift",
            "shifted_domain": shifted,
            "pattern_count": len(patterns),
        },
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": render_patterns_context(patterns, tag="ace-patterns-domain-shift")
            or f"ACE domain shift detected: {shifted}. Re-run scoped retrieval.",
        }
    }


def handle_pre_tool_use(event: dict) -> dict:
    repo_root = _repo_root(event)
    state_dir = _session_state_dir(repo_root, event)
    retrieval_state = load_json(state_dir / "retrieval_state.json", {})
    if retrieval_state.get("needs_search"):
        _log_hook_event(repo_root, event, {"handler": "pre_tool_use", "stage": "blocked_pending_retrieval"})
        return {
            "decision": "block",
            "reason": "ACE retrieval must run before state-changing work. Resolve retrieval first.",
        }
    _log_hook_event(repo_root, event, {"handler": "pre_tool_use", "stage": "allowed"})
    return {}


def handle_stop(event: dict) -> dict:
    repo_root = _repo_root(event)
    state_dir = _session_state_dir(repo_root, event)
    binding = load_workspace_binding(repo_root)
    _log_hook_event(repo_root, event, {"handler": "stop", "stage": "start"})
    if event.get("stop_hook_active"):
        _log_hook_event(repo_root, event, {"handler": "stop", "stage": "skip_continuation"})
        return {"continue": True, "systemMessage": "ACE skipped continuation stop"}

    last_message = event.get("last_assistant_message") or ""
    parsed_review = parse_ace_review(last_message)
    if parsed_review:
        write_json(
            state_dir / "review_result.json",
            {
                "helpful_pct": parsed_review.helpful_pct,
                "time_saved": parsed_review.time_saved,
                "reason": parsed_review.reason,
            },
        )
        write_json(state_dir / "review_request.json", {})
        _log_hook_event(repo_root, event, {"handler": "stop", "stage": "review_result"})
        return {}

    retrieval_state = load_json(state_dir / "retrieval_state.json", {})
    tool_uses = load_json(state_dir / "tool_uses.json", [])
    tool_names = [item.get("tool_name", "") for item in tool_uses]
    prompt = retrieval_state.get("prompt", "") or (event.get("prompt") or "")

    if should_skip_learning(prompt):
        _log_hook_event(repo_root, event, {"handler": "stop", "stage": "skip_learning", "reason": "control_prompt"})
        return {}

    trajectory = []
    for item in tool_uses:
        trajectory.append(
            {
                "tool_name": item.get("tool_name"),
                "input": item.get("tool_input", {}),
                "response": item.get("tool_response", {}),
                "tool_use_id": item.get("tool_use_id"),
                "timestamp": item.get("timestamp"),
            }
        )

    trace = {
        "task": prompt,
        "trajectory": trajectory,
        "result": {
            "success": True,
            "output": f"Executed {len(tool_uses)} tool calls",
            "summary": (event.get("last_assistant_message") or "")[:2000] or None,
        },
        "playbook_used": retrieval_state.get("pattern_ids", []),
        "timestamp": now_iso(),
        "session_id": retrieval_state.get("session_id") or event.get("session_id"),
        "turn_id": event.get("turn_id"),
        "transcript_path": retrieval_state.get("transcript_path") or event.get("transcript_path"),
    }

    learn_result = learn(trace, binding=binding)
    stats = ((learn_result.data or {}).get("learning_statistics") or {}) if learn_result.data else {}
    if "learning_statistics" in stats:
        stats = stats.get("learning_statistics", {})
    if not learn_result.ok or learn_result.returncode != 0:
        write_json(
            state_dir / "learning_result.json",
            {
                "ok": learn_result.ok,
                "returncode": learn_result.returncode,
                "stdout": learn_result.stdout[:2000],
                "stderr": learn_result.stderr[:2000],
                "statistics": stats,
            },
        )
        _log_hook_event(repo_root, event, {"handler": "stop", "stage": "learn_failed", "returncode": learn_result.returncode})
        return {
            "decision": "block",
            "reason": f"ACE learn failed. {learn_result.stderr[:200] or learn_result.stdout[:200] or 'Check ACE learn diagnostics.'}",
        }
    avg_relevance = 0
    patterns = retrieval_state.get("patterns", [])
    if patterns:
        avg_relevance = int(sum(p.get("confidence", 0) for p in patterns) / len(patterns) * 100)
    review_prompt = build_review_request(
        patterns_injected=len(retrieval_state.get("pattern_ids", [])),
        avg_relevance=avg_relevance,
        tools_executed=len(tool_names),
    )
    write_json(state_dir / "review_request.json", {"prompt": review_prompt})
    write_json(
        state_dir / "learning_result.json",
        {
            "ok": learn_result.ok,
            "returncode": learn_result.returncode,
            "stdout": learn_result.stdout[:2000],
            "stderr": learn_result.stderr[:2000],
            "statistics": stats,
        },
    )
    write_json(state_dir / "tool_uses.json", [])
    retrieval_state["needs_search"] = False
    write_json(state_dir / "retrieval_state.json", retrieval_state)
    _log_hook_event(
        repo_root,
        event,
        {
            "handler": "stop",
            "stage": "learned",
            "tool_count": len(tool_uses),
            "pattern_count": len(retrieval_state.get("pattern_ids", [])),
        },
    )
    _log_relevance(
        repo_root,
        event,
        {
            "stage": "stop",
            "prompt": prompt,
            "pattern_count": len(retrieval_state.get("pattern_ids", [])),
            "avg_confidence": (
                sum(p.get("confidence", 0) for p in patterns) / len(patterns)
                if patterns
                else 0.0
            ),
            "domains": retrieval_state.get("known_domains") or [],
            "tool_count": len(tool_uses),
        },
    )
    if retrieval_state.get("pattern_ids"):
        return {"decision": "block", "reason": "Run one more pass and include the ACE_REVIEW line for prior guidance."}
    return {}


def handle_permission_request(event: dict) -> dict:
    command = (event.get("tool_input") or {}).get("command", "")
    decision = permission_decision(command)
    if decision == "allow":
        return {"decision": "allow"}
    return {}


def handle_session_start(event: dict) -> dict:
    repo_root = _repo_root(event)
    state_dir = _session_state_dir(repo_root, event)
    binding = load_workspace_binding(repo_root)
    review_request = load_json(state_dir / "review_request.json", {})
    if review_request.get("prompt"):
        _log_hook_event(repo_root, event, {"handler": "session_start", "stage": "review_prompt"})
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": review_request.get("prompt", ""),
            }
        }
    retrieval_state = load_json(state_dir / "retrieval_state.json", {})
    if not retrieval_state:
        latest_state_dir = latest_session_state_dir(repo_root)
        if latest_state_dir:
            retrieval_state = load_json(latest_state_dir / "retrieval_state.json", {})
    if not retrieval_state:
        _log_hook_event(repo_root, event, {"handler": "session_start", "stage": "start_no_state"})
        return {}
    _log_hook_event(repo_root, event, {"handler": "session_start", "stage": "start"})
    session_id = retrieval_state.get("session_id")
    if session_id:
        recalled = cache_recall(session_id, binding=binding)
        patterns = (recalled.data or {}).get("similar_patterns", []) if recalled.data else []
        if patterns:
            _log_hook_event(repo_root, event, {"handler": "session_start", "stage": "recalled", "pattern_count": len(patterns)})
            return {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": render_patterns_context(patterns, tag="ace-patterns-recalled"),
                }
            }
    _log_hook_event(repo_root, event, {"handler": "session_start", "stage": "resume_context"})
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"ACE resume context: previous task prompt was '{retrieval_state.get('prompt', '')[:200]}'.",
        }
    }


HANDLERS = {
    "user_prompt_submit": handle_user_prompt_submit,
    "pre_tool_use": handle_pre_tool_use,
    "post_tool_use": handle_post_tool_use,
    "stop": handle_stop,
    "permission_request": handle_permission_request,
    "session_start": handle_session_start,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in HANDLERS:
        print("{}", end="")
        return 0
    event = _stdin_json()
    result = HANDLERS[sys.argv[1]](event)
    print(json.dumps(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
