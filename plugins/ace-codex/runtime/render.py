from __future__ import annotations


def format_status_report(
    status: dict | None,
    binding: dict | None,
    review: dict | None,
    hooks: dict | None = None,
) -> str:
    status = status or {}
    binding = binding or {}
    review = review or {}
    hooks = hooks or {}

    playbook = status.get("playbook", {})
    subscription = status.get("subscription") or {}
    usage = subscription.get("usage", {})
    pattern_usage = usage.get("patterns", {})

    lines = [
        "ACE Status",
        f"org_id: {binding.get('org_id', '-')}",
        f"project_id: {binding.get('project_id', '-')}",
        f"verbosity: {binding.get('verbosity', '-')}",
        f"patterns_total: {playbook.get('total_patterns', 0)}",
        f"helpful_total: {playbook.get('helpful_total', 0)}",
        f"harmful_total: {playbook.get('harmful_total', 0)}",
        f"plan: {subscription.get('plan', '-')}",
        f"pattern_usage: {pattern_usage.get('used', 0)}/{pattern_usage.get('limit', 0)}",
    ]

    if hooks:
        lines.extend(
            [
                f"codex_hooks: {hooks.get('status', 'unknown')}",
                f"codex_user_hooks_enabled: {hooks.get('user_hooks_enabled', False)}",
                f"codex_plugin_hooks_enabled: {hooks.get('plugin_hooks_enabled', False)}",
                f"codex_hooks_message: {hooks.get('message', '-')}",
            ]
        )

    if review:
        lines.extend(
            [
                f"last_review_helpful_pct: {review.get('helpful_pct', 0)}",
                f"last_review_time_saved: {review.get('time_saved', '-')}",
                f"last_review_reason: {review.get('reason', '-')}",
            ]
        )

    return "\n".join(lines)


def format_org_choices(payload: dict | None) -> str:
    payload = payload or {}
    orgs = payload.get("organizations", [])
    if not orgs:
        return "No organizations returned by ACE."
    lines = ["Organizations:"]
    for org in orgs:
        lines.append(f"- {org.get('name', org.get('org_id', '-'))}: {org.get('org_id', '-')}" )
    return "\n".join(lines)


def format_project_choices(payload: dict | None) -> str:
    payload = payload or {}
    projects = payload.get("projects", [])
    if not projects:
        return "No projects returned by ACE."
    lines = ["Projects:"]
    for project in projects:
        name = project.get("project_name", project.get("name", project.get("project_id", "-")))
        lines.append(f"- {name}: {project.get('project_id', '-')}")
    return "\n".join(lines)
