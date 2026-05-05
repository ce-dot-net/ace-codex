from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_excludes_local_state():
    text = (ROOT / ".gitignore").read_text()
    assert ".codex/" in text
    assert ".claude/" in text
    assert ".github/.ace-version.json" in text
