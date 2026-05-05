# Releasing ACE Codex

Single source of truth for cutting a new release. Follow these steps in order. Skipping any of them risks shipping a broken plugin to end users because Codex caches by version: a stale cache silently keeps the old code.

## Prerequisites

- Working tree clean (`git status` reports nothing).
- On `main`, up to date with `origin/main`.
- All 86+ pytest tests pass: `python3 -m pytest tests/ -q`.
- `$ace-doctor` reports `verdict: ok` against the current dev install.

## Step 1 — Decide the bump

Follow semver against `plugins/ace-codex/.codex-plugin/plugin.json` `version`:

- `patch` (`0.1.x`) — docs, release hygiene, internal refactors with no behavior change
- `minor` (`0.x.0`) — backwards-compatible workflow additions (new skills, new optional config, new hook handlers)
- `major` (`x.0.0`) — breaking changes to manifest, hook contracts, runtime state layout, or `.codex/ace.json` schema

## Step 2 — Bump every version reference

The plugin version lives in **one** place that the runtime reads, but ships are easy to break if any of these drift. Update every match in a single edit pass:

| File | What to update |
|---|---|
| `plugins/ace-codex/.codex-plugin/plugin.json` | `"version"` (single source of truth — Codex caches by this value) |
| `CHANGELOG.md` | Insert a new `## <version>` section above the previous one with one bullet per behavior change |
| `docs/ace-codex-port-backlog.md` | Update `## Current status (<version>)` heading |
| `plugins/ace-codex/docs/TROUBLESHOOTING.md` | Only if the release fixes a documented failure mode — add a new `verdict:` entry; never edit the historical fix-story bullets |

`README.md`, `plugins/ace-codex/README.md`, and `INSTALL.md` should not contain the version number — they reference flows, not pinned versions, so they don't drift.

## Step 3 — Validate

Run all of these. Each must succeed before commit:

```bash
python3 -m py_compile plugins/ace-codex/runtime/{ace_cli,ace_codex,config,workspace,render,hook_entry}.py
python3 -c "import json; [json.load(open(f)) for f in ['plugins/ace-codex/.codex-plugin/plugin.json','plugins/ace-codex/.mcp.json','plugins/ace-codex/hooks/hooks.json','.agents/plugins/marketplace.json']]"
python3 -m pytest tests/ -q
bash plugins/ace-codex/scripts/ace-doctor.sh
```

Expected: 86+ tests pass, no JSON parse errors, no python syntax errors, doctor `verdict: ok`.

## Step 4 — Commit

One conventional-commit message summarising every behavior change. Reference the version in the subject:

```
release: v<version> — <one-line summary>

<bullet list of behavior changes, one per CHANGELOG entry>
```

Do **not** amend the prior commit. Always create a new commit so `last_revision` in `~/.codex/config.toml` advances.

## Step 5 — Push and tag

```bash
git push
gh release create v<version> \
  --title "v<version> — <one-line summary>" \
  --notes "$(awk "/^## $VERSION$/,/^## /" CHANGELOG.md | sed '$d')"
```

Replace `$VERSION` with the new version. The `awk` pulls the matching CHANGELOG section as release notes.

## Step 6 — Verify the install path end to end

This catches issues that only surface against a real github-backed marketplace pull:

```bash
codex plugin marketplace upgrade ce-dot-net
ls ~/.codex/plugins/cache/ce-dot-net/ace-codex/   # should list the new <version> dir
```

Then in a fresh Codex thread:

1. `$ace-doctor` should report `plugin_version_drift: False` and `verdict: ok`.
2. Send a small prompt that exercises retrieval + learn (e.g. "list the runtime python modules and explain each").
3. Confirm `<ace-patterns>` appears in the TUI hook context line.
4. Wait for `Stop hook (completed)` — `learning_result.json` should appear under `.codex/.ace-codex/sessions/<sid>/` with `"ok": true`.

If any of these fail, open an issue tagging the release and either roll back (`gh release delete v<version> --cleanup-tag`) or ship a patch immediately.

## Files Codex actually loads (don't break these)

A breaking change to any of these requires a major bump:

- `plugins/ace-codex/.codex-plugin/plugin.json` — manifest, must declare `mcpServers`, `hooks`, `skills`
- `plugins/ace-codex/.mcp.json` — must wrap servers under `mcp_servers` or use the direct map shape
- `plugins/ace-codex/hooks/hooks.json` — must wrap events under the outer `"hooks"` key (this trapped 0.1.0–0.1.14)
- `plugins/ace-codex/runtime/hook_entry.py` — module imports must stay compatible with the layered `from ace_codex import …` pattern
- `.agents/plugins/marketplace.json` — must declare `source.path: ./plugins/ace-codex` for git-backed installs

## Common pitfalls

- **Forgetting `[features].plugin_hooks = true`** — `$ace-configure` writes it; users who skipped configure see "no hooks fire". Document in INSTALL.md, not in the release notes.
- **Editing only the manifest version** — Codex caches by `<version>` directory name. If you bump the manifest but a user has the old version cached, they keep running the old code. The CHANGELOG and `git push` make sure `last_revision` advances and `marketplace upgrade` re-fetches.
- **Splitting one fix across two releases** — every `verdict:` change in `$ace-doctor` should ship in the same release as the underlying fix; otherwise users see a verdict that names a fix that isn't in their cache yet.
- **Using `git commit --amend`** — breaks `last_revision` tracking on Codex's side because the SHA doesn't match what was already pulled.
