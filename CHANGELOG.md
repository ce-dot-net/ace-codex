# Changelog

## 0.1.20

- Docs-only fix for the release notes recipe in `RELEASING.md` and `.claude/agents/release-manager.md`. The previous `awk … | sed '$d'` form broke under shell escaping (the `$d` was interpreted as a shell variable inside double quotes, leaving `gh release create` with empty notes). New form uses `awk -v ver="## $VERSION" '$0 == ver …'` so the version interpolates safely and the awk body stays single-quoted. Both files now also include an empty-notes guard that bails before `gh release create` if extraction failed
- Bumping the manifest in lockstep so end-user installs see the doc fix without manual `git pull`

## 0.1.19

- Cleaner `<ace-patterns>` injection on `UserPromptSubmit`. The previous renderer dumped up to 8 raw patterns including full code-block bodies (one observed turn shipped 2594 chars of context with a 636-char fenced subprocess example). New renderer:
  - keeps top 10 patterns in ace-cli's existing relevance order (no local re-sort, the backend's ranking is authoritative)
  - drops patterns whose body is mostly a fenced code block — those bloat the model's developer context and rarely help inline guidance
  - collapses whitespace and trims each pattern's content to 120 chars with a trailing ellipsis
  - caps total output at 1500 chars; remaining patterns are dropped silently rather than truncating mid-line
- Net effect on the live JWT-authentication test: 14 raw patterns → 1364-char tag (47% of the previous payload) with the proven-helpful pattern still first
- Added pytest coverage for the new behavior: code-block drop, total-length cap, ace-cli relevance order preservation, empty input

## 0.1.18

- Phase 1 — ported 14 missing skills from the Claude ACE plugin to Codex-native `$ace-*` skills: `ace-search`, `ace-patterns`, `ace-top`, `ace-domains`, `ace-learn`, `ace-clear`, `ace-export-patterns`, `ace-import-patterns`, `ace-delta`, `ace-tune`, `ace-test`, `ace-install-cli`, `ace-cleanup`, `ace-insights`. Each is a `SKILL.md` under `plugins/ace-codex/skills/<name>/` with frontmatter that describes both **what** and **when** so Codex's implicit description-match invokes them correctly
- Added wrapper scripts where shell logic is needed: `scripts/ace-test.sh` (lightweight self-test), `scripts/ace-cleanup.sh` (dry-run + delete-sessions + delete-all modes for local state), `scripts/ace-insights.sh` (md/html/json relevance report from `relevance.jsonl`)
- Phase 2 — bundled an MCP server: `plugins/ace-codex/.mcp.json` registers `ace-pattern-learning` via `npx --yes @ce-dot-net/ace-client@latest`, mirroring the Claude plugin. The plugin manifest's new `"mcpServers": "./.mcp.json"` field auto-loads it on install
- Phase 2 — added `relevance.jsonl` per-session log written by both `UserPromptSubmit` and `Stop` handlers. Schema: `timestamp`, `session_id`, `turn_id`, `prompt`, `pattern_count`, `avg_confidence`, `domains`, `tool_count`, `stage`. Consumed by `$ace-insights` to render markdown/html/json reports
- Phase 3 — added authoritative documentation under `plugins/ace-codex/docs/`:
  - `ARCHITECTURE.md` — Generator/Reflector/Curator role mapping, hook lifecycle, state directory layout, ace-cli transport rationale, hook command shape, two-flag gating
  - `SECURITY.md` — credentials, network surface, permission auto-allow allowlist, sandbox compatibility, exact trace payload schema, reset paths, known limitations
  - `TROUBLESHOOTING.md` — verdict-by-verdict remediation referencing `$ace-doctor` output

## 0.1.17

- **Domain-shift detection: fixed (was dead code since 0.1.0).** Codex hook events deliver `tool_input = {"command": "..."}` for both `Bash` and `apply_patch` — there is no `file_path` field like Claude Code's `Edit/Write/Read` tools. Our PostToolUse handler short-circuited on `if not file_path: return {}`, so domain-shift re-search never ran. Added `extract_codex_file_paths(tool_name, tool_input)` that:
  - For `apply_patch`: regex-extracts every `*** (Add|Update|Delete) File: <path>` header from the patch body
  - For `Bash`: heuristically pulls the last argument that looks like a source file (slash + recognised code extension); deliberately conservative to avoid spamming re-search for non-edit commands
- Wired the extractor into `handle_post_tool_use` so domain shifts now actually fire when codex applies a patch or runs a file-targeted shell command
- Confirmed `$ace-bootstrap` end-to-end with `ace-cli bootstrap --json --mode hybrid --thoroughness medium --org … --project …` → returns `{"success": true, "patternsExtracted": 5, …}` in ~3s. Bootstrap script flag set is correct
- Verified Codex has no `PreCompact` / `SessionEnd` / `SubagentStop` / `Notification` hook events (only the 6 in `codex-rs/hooks/src/lib.rs:HOOK_EVENT_NAMES`). Replacement for PreCompact is implicit: `Stop` is turn-scoped in Codex (fires after every turn, not session-end), so `learning_result.json`, `tool_uses.json` clearing, and `review_request.json` are flushed to disk every turn. Compaction can't lose ACE state because state is persisted before any context shrink

## 0.1.16

- Switched `ace-cli learn` invocation from `--stdin` to `--transcript <tempfile>`. Codex's nested hook subprocess context (`/bin/sh -lc` → `python3 hook_entry.py` → `subprocess.run(input=…)`) reproducibly trips a Node-side "Failed to read from stdin" error in `ace-cli` even though the stdin pipe is technically intact. Writing the trace to a temp file and pointing `--transcript` at it bypasses the Node TTY/pipe race entirely. Search retrieval (`UserPromptSubmit`) keeps using `--stdin` because it works in practice for short query payloads, but the same pattern can be applied if ever needed
- Added test asserting the new transport (`--transcript` present, `--stdin` absent, no piped `stdin_text`)

## 0.1.15

- **Real root cause for silent hooks (verified by reading Codex source `codex-rs/config/src/hook_config.rs:11-13`):** Codex's `HooksFile` deserializer expects an outer `{"hooks": {...}}` wrapper around the event map. Our previous `hooks/hooks.json` placed events at the top level without that wrapper. Because `HooksFile.hooks` is `#[serde(default)]`, the missing wrapper produced an empty `HookEventsToml::default()` and Codex registered **zero handlers** — completely silently, no warning. Plugin showed as enabled, manifest parsed cleanly, plugin_hooks feature on, but the engine had nothing to dispatch
- Fix: wrap the entire event map under the canonical `"hooks"` key. Confirmed by docs example at https://developers.openai.com/codex/hooks#config-shape and matches the wire format used by the Claude ACE plugin's working `hooks.json`. Earlier `0.1.13`/`0.1.14` releases were broken by this missing wrapper despite all other gates being correct
- This is independent of the `[features].plugin_hooks = true` flag work in 0.1.13 — both fixes are required for end-to-end hook firing

## 0.1.14

- Hook commands now prefer the codex-native `${PLUGIN_ROOT}` env var (set by Codex's hook engine to the plugin's installed cache path) over the previous fragile glob fallback. `${CLAUDE_PLUGIN_ROOT}` is also exported by Codex for cross-compat — verified in `codex-rs/hooks/src/engine/discovery.rs` lines 175-180. Glob fallback is kept as a last resort if `PLUGIN_ROOT` is somehow unset
- Each hook command writes a one-line stderr marker (`ACE hook fired: <Event> at <ts> PLUGIN_ROOT=<path>`) so end users can confirm the hook actually executed even before Python state files are produced. Codex captures the stderr in `HookCompletedEvent` and surfaces it via TUI / `codex-tui.log`
- Verified against pinned `rust-v0.128.0` source: `Feature::PluginHooks` (key `plugin_hooks`, UnderDevelopment, default OFF) gates `effective_plugin_hook_sources()`. Without `[features].plugin_hooks = true`, `Hooks::new` receives an empty `plugin_hook_sources` vec and our manifest's `hooks/hooks.json` is silently dropped before discovery runs
- Smoke test confirms the new command produces the expected stderr marker, stdout JSON (`hookSpecificOutput.additionalContext`), and `.codex/.ace-codex/sessions/<id>/hook_events.jsonl` log entries

## 0.1.13

- **Root cause fix for silent hooks:** Codex source (`codex-rs/features/src/lib.rs`) defines two separate hook flags. `hooks` (alias `codex_hooks`) is Stable and default-ON for `~/.codex/hooks.json` and `<repo>/.codex/hooks.json`. `plugin_hooks` is "UnderDevelopment" and **default-OFF** for plugin-bundled `hooks/hooks.json`. The ACE plugin uses bundled hooks, so without `[features].plugin_hooks = true` the entire hook pipeline is silently ignored. This was the actual reason ACE retrieval and learning never fired even with `codex_hooks = true` set
- `$ace-configure` now writes `[features].plugin_hooks = true` to `~/.codex/config.toml` (and leaves the canonical `hooks` flag alone since it defaults to true)
- `codex_hooks_status()` now reports `user_hooks_enabled` and `plugin_hooks_enabled` independently and only marks the system enabled when both are on
- `$ace-doctor` verdict line now distinguishes `missing_plugin_hooks_flag` from a generic "hooks disabled" failure and tells the user exactly which `[features]` key to add
- Hardened native hook command paths so end-user installs no longer rely on dev-time relative paths. Cache fallback now honors `${CODEX_HOME:-$HOME/.codex}` and matches any marketplace name via `*/ace-codex/*` glob
- Added `timeout` and `statusMessage` to every hook entry per Codex hook docs and dropped the unsupported `clear` SessionStart matcher (only `startup|resume` are valid)
- Extended `$ace-doctor` diagnosis: detects plugin version drift between the repo manifest and the installed `~/.codex/plugins/cache/*/ace-codex/*/` bundle, reports `[plugins."ace-codex@<marketplace>"]` enablement, surfaces recent hook fire counts per handler from `.codex/.ace-codex/sessions/*/hook_events.jsonl`
- Allowed `ace-doctor.sh` to run from any cwd by falling back to the installed runtime under `${CODEX_HOME}/plugins/cache/*/ace-codex/*/runtime/` when the repo runtime dir is not present

## 0.1.12

- Added explicit per-session hook event traces so prompt, tool, and stop hooks leave a visible audit trail when they fire
- Hardened runtime-state fallback so Codex can write hook state to `CODEX_HOME`, then to the system temp directory if the home fallback is not writable
- Kept the always-on retrieval and learn flow intact for real user prompts and stop events

## 0.1.11

- Made ACE retrieval always-on for real user prompts instead of keyword-gated only
- Made ACE learning at stop-time run even when no state-changing tools were used, while still skipping explicit control commands
- Tightened control-prompt handling so `/ace-*`, `@ace-*`, and `$ace-*` commands do not get forced through the always-on path

## 0.1.10

- Added a runtime-state fallback for read-only `.codex` workspaces so installed users can still get session and review state under `CODEX_HOME/ace-codex/<workspace-key>/`
- This keeps enforcement and trajectory tracking working in Codex sessions even when the repo-local `.codex` directory is not writable

## 0.1.9

- Bumped the plugin version again so a fresh Codex reinstall cannot reuse the stale `0.1.7` cache cut
- This is a release-key refresh only; the `ace-doctor` fix remains the same

## 0.1.8

- Fixed `ace-doctor` skill to use the repo status wrapper instead of raw non-interactive `ace-cli status --json`
- Kept the raw CLI path explicit with `--org` and `--project` for manual diagnosis

## 0.1.7

- Forced a fresh Codex cache key so reinstall/update cannot reuse the stale `ace-status` bundle
- Keeps `ace-status` on the repo wrapper path and avoids the old raw non-interactive fallback

## 0.1.6

- Fixed `ace-status` skill to invoke the repo wrapper instead of raw non-interactive `ace-cli status --json`
- Kept raw CLI usage explicit and bound by `--org` and `--project` for non-interactive status checks

## 0.1.5

- Removed MCP-style matcher references from hooks and runtime tool-state matching
- Kept ACE enforcement on `ace-cli` plus native Codex hooks only

## 0.1.4

- Moved ACE runtime state to native Codex session-scoped storage under `.codex/.ace-codex/sessions/<session_id>/`
- Kept shared domain-shift state workspace-scoped under `.codex/.ace-codex/workspace/`
- Updated review and status surfaces to read the latest session state safely
- Added Codex-like hook CLI payload tests and isolated-home marketplace registration tests

## 0.1.3

- Hardened native Codex hook runtime across repo-root, workspace-root, and installed cache execution paths
- `ace-configure` now writes `.codex/ace.json` and enables `features.codex_hooks = true` in Codex config
- Broadened engineering prompt detection and improved same-domain scope-shift retrieval refresh
- Clarified enduser reinstall/new-thread flow for plugin updates and hook activation

## 0.1.2

- Clarified Codex-native invocation: use `@ace-codex` and `$ace-*`, not Claude-style slash commands
- Added fail-closed diagnostics for missing `features.codex_hooks = true`
- Fixed `ace-status` rendering when ACE returns `"subscription": null`

## 0.1.1

- Public release hardening for marketplace distribution
- Removed local-state files from the published repo
- Added a public example binding template for onboarding
- Clarified install flow and versioning policy

## 0.1.0

- Initial marketplace plugin scaffold
- Codex-native skills, hooks, runtime, and ACE CLI wrappers
