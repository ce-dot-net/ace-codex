# Troubleshooting

Run `$ace-doctor` first. It prints a single-line `verdict:` that names the most likely failure mode. The rest of this document explains what each failure mode means and how to fix it.

## `verdict: SET [features].plugin_hooks = true …`

Plugin-bundled hooks are gated behind a separate experimental feature flag from the user-level hook loader. `[features].codex_hooks = true` is only an alias for the canonical `hooks` flag, which is on by default. The flag we actually need is `plugin_hooks`.

Fix:
1. Run `$ace-configure`. It writes `plugin_hooks = true` automatically.
2. Restart Codex. Resume does **not** rebuild the hook engine — a full quit + relaunch is required.
3. Re-run `$ace-doctor`. Verdict should change.

## `verdict: cached plugin version != repo manifest …`

Codex installs plugins into `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` and only loads the cached copy at session start. If the repo manifest has been bumped without a marketplace upgrade, the running session is on the old code.

Fix:
```bash
codex plugin marketplace upgrade <marketplace>
```
Then restart Codex.

## `verdict: plugin not registered in ~/.codex/config.toml …`

The marketplace was added but the plugin was never enabled in the Codex plugin directory.

Fix:
1. Open Codex's plugin directory (`/plugins`).
2. Pick the marketplace and install `ace-codex`.
3. Confirm `[plugins."ace-codex@<marketplace>"] enabled = true` is in `~/.codex/config.toml`.

## `verdict: hooks never fired …`

All flags and registrations look correct, but no `hook_events.jsonl` exists yet under `.codex/.ace-codex/sessions/`. Most common causes:

- The current Codex session was started **before** `plugin_hooks` was enabled. Quit and relaunch Codex.
- The project is not trusted. Codex prompts on first session; check `[projects."<repo path>"].trust_level = "trusted"` in `~/.codex/config.toml`.
- Codex was launched in a directory without project root markers. Set `project_root_markers = []` or open the repo via `cd` before running `codex`.

## `Stop hook (blocked) feedback: ACE learn failed. {"level":"error","message":"Failed to read from stdin"}`

This was a known bug in 0.1.15 and earlier where `ace-cli learn --stdin` failed inside the nested hook subprocess context. Fixed in 0.1.16 by switching to `--transcript <tempfile>`.

Fix: upgrade the plugin.
```bash
codex plugin marketplace upgrade <marketplace>
```

## `verdict: ok` but no patterns are injected

Doctor reports green but `<ace-patterns>` never appears in TUI on UserPromptSubmit. The playbook is empty — this is normal for a freshly configured project.

Fix: run `$ace-bootstrap` to seed the playbook from the codebase. After bootstrap, prompts trigger pattern retrieval.

## `command not found: ace-cli`

Run `$ace-install-cli`. If `npm install -g @ace-sdk/cli` fails with EACCES, point `npm` at a user-writable prefix:
```bash
npm config set prefix ~/.npm-global
export PATH="$HOME/.npm-global/bin:$PATH"
```
Or use a Node version manager (nvm, fnm, asdf) so the global install lives in a per-user dir.

## `Under-development features enabled: plugin_hooks` warning at startup

Expected behavior. `plugin_hooks` is staged as `UnderDevelopment` upstream. The warning is informational; the plugin works correctly. To suppress:
```toml
suppress_unstable_features_warning = true
```
in `~/.codex/config.toml`.

## Repeated `Failed to find expected lines in …` errors

Not an ACE issue. This is Codex's `apply_patch` tool reporting a stale patch. Ask Codex to re-read the file before patching.

## Need a clean reset

```bash
$ace-cleanup     # default dry-run; print scope
# then re-run with mode = delete-sessions or delete-all
```
This wipes local session state but leaves the server-side playbook and the repo binding intact. To wipe the playbook itself, use `$ace-clear` (destructive; prompts for confirmation).
