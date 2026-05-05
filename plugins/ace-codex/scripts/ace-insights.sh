#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
FORMAT="${2:-md}"  # md | html | json
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"

WORKSPACE_KEY="$(python3 - "$REPO_ROOT" <<'PY'
import hashlib, sys
from pathlib import Path
print(hashlib.sha1(str(Path(sys.argv[1]).resolve()).encode("utf-8")).hexdigest()[:12])
PY
)"

python3 - "$REPO_ROOT" "$CODEX_HOME_DIR/ace-codex/$WORKSPACE_KEY" "$FORMAT" <<'PY'
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

repo_root = Path(sys.argv[1])
home_state = Path(sys.argv[2])
fmt = sys.argv[3]

session_dirs: list[Path] = []
for base in (repo_root / ".codex" / ".ace-codex" / "sessions", home_state / "sessions"):
    if base.exists():
        session_dirs.extend(p for p in base.iterdir() if p.is_dir())

rows: list[dict] = []
for session in session_dirs:
    log = session / "relevance.jsonl"
    if not log.exists():
        continue
    for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except Exception:
            continue

rows.sort(key=lambda r: r.get("timestamp") or "", reverse=True)

if fmt == "json":
    json.dump(rows, sys.stdout, indent=2)
    sys.stdout.write("\n")
    sys.exit(0)

if not rows:
    print("No ACE relevance entries found yet. Run a few real tasks; the PostToolUse and Stop hooks will populate `relevance.jsonl` automatically.")
    sys.exit(0)

if fmt == "html":
    out_path = repo_root / f"ace-insights-{datetime.utcnow():%Y%m%d}.html"
    body = ["<table><tr><th>Time</th><th>Prompt</th><th>Patterns</th><th>Avg conf</th><th>Domains</th><th>Tools</th></tr>"]
    for r in rows:
        body.append(
            "<tr>"
            f"<td>{r.get('timestamp','')}</td>"
            f"<td>{(r.get('prompt') or '')[:100]}</td>"
            f"<td>{r.get('pattern_count',0)}</td>"
            f"<td>{r.get('avg_confidence',0):.2f}</td>"
            f"<td>{','.join(r.get('domains') or [])}</td>"
            f"<td>{r.get('tool_count',0)}</td>"
            "</tr>"
        )
    body.append("</table>")
    out_path.write_text(
        "<!doctype html><meta charset=utf-8><title>ACE insights</title>"
        "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.4rem .8rem}</style>"
        + "".join(body)
    )
    print(f"Wrote {out_path}")
    sys.exit(0)

# Default: Markdown
print("| time | prompt | patterns | avg conf | domains | tools |")
print("|------|--------|----------|----------|---------|-------|")
for r in rows:
    prompt = (r.get("prompt") or "").replace("|", "\\|")[:80]
    domains = ",".join(r.get("domains") or [])
    print(
        f"| {r.get('timestamp','')} | {prompt} | {r.get('pattern_count',0)} | "
        f"{r.get('avg_confidence',0):.2f} | {domains} | {r.get('tool_count',0)} |"
    )
PY
