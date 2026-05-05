from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CLI_CMD = "ace-cli"


@dataclass
class CLIResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    data: Any = None


def _base_env(binding: dict | None = None) -> dict:
    env = os.environ.copy()
    if binding:
        org_id = binding.get("org_id")
        project_id = binding.get("project_id")
        verbosity = binding.get("verbosity")
        if org_id:
            env["ACE_ORG_ID"] = org_id
        if project_id:
            env["ACE_PROJECT_ID"] = project_id
        if verbosity:
            env["ACE_VERBOSITY"] = verbosity
    return env


def run_json(args: list[str], binding: dict | None = None, stdin_text: str | None = None, timeout: int = 30) -> CLIResult:
    env = _base_env(binding)
    try:
        result = subprocess.run(
            [CLI_CMD, *args],
            input=stdin_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        return CLIResult(False, 127, "", "ace-cli not found")
    except subprocess.TimeoutExpired:
        return CLIResult(False, 124, "", "ace-cli timed out")

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    try:
        data = json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        data = None
    return CLIResult(result.returncode == 0, result.returncode, stdout, stderr, data)


def whoami() -> CLIResult:
    return run_json(["whoami", "--json"], timeout=10)


def status(binding: dict | None = None) -> CLIResult:
    args = ["status", "--json"]
    if binding:
        org_id = binding.get("org_id")
        project_id = binding.get("project_id")
        if org_id:
            args.extend(["--org", org_id])
        if project_id:
            args.extend(["--project", project_id])
    return run_json(args, binding=binding, timeout=20)


def orgs() -> CLIResult:
    return run_json(["orgs", "--json"], timeout=20)


def projects(org_id: str) -> CLIResult:
    return run_json(["projects", "--org", org_id, "--json"], timeout=20)


def switch_org(org_id: str) -> CLIResult:
    return run_json(["switch-org", org_id], timeout=20)


def search(query: str, binding: dict, session_id: str | None = None, allowed_domains: list[str] | None = None) -> CLIResult:
    args = ["search", "--stdin", "--json"]
    if session_id:
        args.extend(["--pin-session", session_id])
    if allowed_domains:
        for domain in allowed_domains:
            args.extend(["--allowed-domains", domain])
    return run_json(args, binding=binding, stdin_text=query, timeout=30)


def cache_recall(session_id: str, binding: dict) -> CLIResult:
    return run_json(["cache", "recall", "--session", session_id, "--json"], binding=binding, timeout=10)


def bootstrap(binding: dict, mode: str = "hybrid", thoroughness: str = "medium", extra_args: list[str] | None = None) -> CLIResult:
    args = ["bootstrap", "--json", "--mode", mode, "--thoroughness", thoroughness]
    if extra_args:
        args.extend(extra_args)
    return run_json(args, binding=binding, timeout=300)


def learn(trace: dict, binding: dict) -> CLIResult:
    """
    Submit an execution trace to `ace-cli learn`.

    Uses `--transcript <file>` instead of `--stdin` because Codex's nested hook
    subprocess context produces "Failed to read from stdin" when ace-cli (Node)
    tries to read from a piped stdin inherited through `/bin/sh -lc` →
    `python3 hook_entry.py` → `subprocess.run(input=...)`. Writing the trace to
    a temp file avoids the Node TTY/pipe race entirely.
    """
    verbosity = binding.get("verbosity", "detailed")
    tmp_dir = Path(tempfile.gettempdir())
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="ace-trace-",
        suffix=".json",
        dir=str(tmp_dir),
        delete=False,
    ) as handle:
        handle.write(json.dumps(trace))
        transcript_path = handle.name
    try:
        args = [
            "learn",
            "--transcript",
            transcript_path,
            "--timeout",
            "300000",
            "--verbosity",
            verbosity,
        ]
        return run_json(args, binding=binding, timeout=300)
    finally:
        try:
            os.unlink(transcript_path)
        except OSError:
            pass
