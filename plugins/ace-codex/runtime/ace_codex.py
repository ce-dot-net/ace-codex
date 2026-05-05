from __future__ import annotations

import json
import re
import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


IMPLEMENTATION_KEYWORDS = (
    "implement",
    "build",
    "create",
    "fix",
    "debug",
    "refactor",
    "optimize",
    "migrate",
    "update",
    "add",
    "modify",
    "change",
    "edit",
    "enhance",
    "extend",
    "troubleshoot",
    "resolve",
    "diagnose",
    "integrate",
    "connect",
    "setup",
    "configure",
)

CONTROL_PROMPT_PATTERNS = (
    r"^/(plugins?|help|status)\b",
    r"^/ace[-:]",
    r"^@(ace-codex|ace-login|ace-configure|ace-bootstrap|ace-status)\b",
    r"^\$(ace-codex|ace-login|ace-configure|ace-bootstrap|ace-status)\b",
)

STATE_CHANGING_TOOL_MATCHERS = ("Edit", "Write", "Bash", "apply_patch", "NotebookEdit")
SAFE_PERMISSION_PREFIXES = ("ace-cli search", "ace-cli cache recall", "ace-cli learn", "ace-cli whoami", "ace-cli status")
ACE_REVIEW_RE = re.compile(r"ACE_REVIEW:\s*(?P<pct>\d+)%?\s*\|\s*(?P<time>[^|]+?)\s*\|\s*(?P<reason>.+)")


@dataclass
class ACEReview:
    helpful_pct: int
    time_saved: str
    reason: str


def classify_prompt_for_search(prompt: str) -> bool:
    text = prompt.strip().lower()
    if not text:
        return False
    if any(re.search(pattern, text) for pattern in CONTROL_PROMPT_PATTERNS):
        return False
    return True


def should_skip_learning(prompt: str) -> bool:
    text = prompt.strip().lower()
    return not text or any(re.search(pattern, text) for pattern in CONTROL_PROMPT_PATTERNS)


def has_substantial_work(tool_names: list[str]) -> bool:
    return any(any(marker in name for marker in STATE_CHANGING_TOOL_MATCHERS) for name in tool_names)


APPLY_PATCH_FILE_HEADER_RE = re.compile(
    r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$",
    re.MULTILINE,
)
# Heuristic: a Bash arg looks like a path if it contains a slash and ends in
# one of these common code extensions. Avoid catching ad-hoc tokens.
BASH_FILE_ARG_RE = re.compile(
    r"(?:^|\s)((?:[\w./~-]|\\ )+\.(?:py|ts|tsx|js|jsx|rs|go|java|rb|php|c|cc|cpp|h|hpp|sh|bash|zsh|md|toml|json|yaml|yml|sql|html|css|scss|vue|svelte))(?=\s|$)"
)


def extract_codex_file_paths(tool_name: str, tool_input: dict) -> list[str]:
    """
    Codex hook events deliver `tool_input = {"command": "..."}` for both Bash
    and apply_patch — there is no `file_path` field. Pull file paths out of the
    command text so domain-shift detection has something to work with.
    """
    command = (tool_input or {}).get("command")
    if not command or not isinstance(command, str):
        return []

    if tool_name == "apply_patch":
        return [match.strip() for match in APPLY_PATCH_FILE_HEADER_RE.findall(command) if match.strip()]

    if tool_name == "Bash":
        # Only the last looks-like-a-source-file argument; Bash commands often
        # touch many irrelevant paths and we don't want to spam re-search.
        matches = BASH_FILE_ARG_RE.findall(command)
        return [matches[-1]] if matches else []

    return []


def _matched_domain(file_path: str, known_domains: list[str]) -> str | None:
    words = set(re.split(r"[/._-]+", file_path.lower()))
    for domain in known_domains:
        domain_words = [part for part in domain.lower().split("-") if len(part) >= 3]
        if any(word in words for word in domain_words):
            return domain
    return None


def _path_scope(file_path: str) -> tuple[str, str]:
    path = Path(file_path)
    return (path.parent.as_posix(), path.suffix.lower())


def detect_domain_shift(
    file_path: str,
    known_domains: list[str],
    last_domain: str | None = None,
    last_file_path: str | None = None,
) -> str | None:
    domain = _matched_domain(file_path, known_domains)
    if not domain:
        return None
    if domain != last_domain:
        return domain
    if last_file_path and _path_scope(file_path) != _path_scope(last_file_path):
        return domain
    return None


def parse_ace_review(message: str) -> ACEReview | None:
    match = ACE_REVIEW_RE.search(message)
    if not match:
        return None
    return ACEReview(
        helpful_pct=int(match.group("pct")),
        time_saved=match.group("time").strip(),
        reason=match.group("reason").strip(),
    )


def repo_state_dir(repo_root: Path) -> Path:
    return repo_root / ".codex" / ".ace-codex"


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def _repo_state_writable(repo_root: Path) -> bool:
    codex_dir = repo_root / ".codex"
    try:
        if codex_dir.exists():
            return os.access(codex_dir, os.W_OK | os.X_OK)
        return os.access(repo_root, os.W_OK | os.X_OK)
    except Exception:
        return False


def runtime_state_dir(repo_root: Path) -> Path:
    if _repo_state_writable(repo_root):
        return repo_state_dir(repo_root)
    workspace_key = hashlib.sha1(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:12]
    codex_home_dir = codex_home() / "ace-codex" / workspace_key
    try:
        codex_home_dir.mkdir(parents=True, exist_ok=True)
        return codex_home_dir
    except Exception:
        temp_root = Path(tempfile.gettempdir()) / "ace-codex" / workspace_key
        temp_root.mkdir(parents=True, exist_ok=True)
        return temp_root


def workspace_state_dir(repo_root: Path) -> Path:
    return runtime_state_dir(repo_root) / "workspace"


def sessions_state_dir(repo_root: Path) -> Path:
    return runtime_state_dir(repo_root) / "sessions"


def session_key(session_id: str | None) -> str:
    value = (session_id or "codex-session").strip() or "codex-session"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value)


def session_state_dir(repo_root: Path, session_id: str | None) -> Path:
    return sessions_state_dir(repo_root) / session_key(session_id)


def latest_session_state_dir(repo_root: Path) -> Path | None:
    sessions_dir = sessions_state_dir(repo_root)
    if not sessions_dir.exists():
        return None
    candidates = [path for path in sessions_dir.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def repo_config_path(repo_root: Path) -> Path:
    return repo_root / ".codex" / "ace.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True))
        handle.write("\n")


def hook_events_path(repo_root: Path, session_id: str | None) -> Path:
    return session_state_dir(repo_root, session_id) / "hook_events.jsonl"


def build_review_request(patterns_injected: int, avg_relevance: int, tools_executed: int) -> str:
    return (
        f"Review prior ACE guidance as a human developer. {patterns_injected} patterns were injected "
        f"at roughly {avg_relevance}% relevance and {tools_executed} tools executed. "
        "Reply with: ACE_REVIEW: N% | Xm saved | one-line reason"
    )


def permission_decision(command: str) -> str | None:
    normalized = " ".join(command.split())
    for prefix in SAFE_PERMISSION_PREFIXES:
        if normalized.startswith(prefix):
            return "allow"
    return None


def search_warning_message(prompt: str) -> str:
    return f"ACE retrieval should run before state-changing work for: {prompt[:160]}"


_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")
PATTERN_RENDER_TOP_K = 10
PATTERN_RENDER_PER_LINE_CHARS = 120
PATTERN_RENDER_MAX_TOTAL_CHARS = 1500


def _is_mostly_code(content: str) -> bool:
    stripped = content.lstrip()
    return stripped.startswith("```") or content.count("```") >= 2


def _trim_pattern_content(content: str, max_chars: int = PATTERN_RENDER_PER_LINE_CHARS) -> str:
    cleaned = _CODE_BLOCK_RE.sub("[code omitted]", content)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def summarize_pattern(pattern: dict) -> str:
    domain = pattern.get("domain", "general")
    confidence = pattern.get("confidence", 0)
    helpful = pattern.get("helpful", 0)
    content = _trim_pattern_content(pattern.get("content", ""))
    return f"[{domain}] {content} (conf={confidence:.2f}, helpful={helpful})"


def render_patterns_context(
    patterns: list[dict],
    tag: str = "ace-patterns",
    top_k: int = PATTERN_RENDER_TOP_K,
    max_total_chars: int = PATTERN_RENDER_MAX_TOTAL_CHARS,
) -> str:
    """
    Render retrieved patterns as a compact `<ace-patterns>` block.

    Trusts ace-cli's relevance ranking (no local re-sort) so the most
    semantically relevant pattern stays first. Drops patterns whose body is
    mostly a code block — those are too long for inline injection and rarely
    useful as guidance. Each pattern's content is collapsed to a single line
    and trimmed to `PATTERN_RENDER_PER_LINE_CHARS`. Total output is capped at
    `max_total_chars` to avoid bloating the model's developer context.
    """
    if not patterns:
        return ""
    pool = [p for p in patterns if not _is_mostly_code(p.get("content", ""))]
    lines: list[str] = []
    total = len(tag) * 2 + len("<></>") + 2
    for pattern in pool[:top_k]:
        line = f"- {summarize_pattern(pattern)}"
        if total + len(line) + 1 > max_total_chars:
            break
        lines.append(line)
        total += len(line) + 1
    if not lines:
        return ""
    return f"<{tag}>\n" + "\n".join(lines) + f"\n</{tag}>"


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
