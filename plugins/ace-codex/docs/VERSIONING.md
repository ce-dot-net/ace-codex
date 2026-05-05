# Versioning

Codex plugins are versioned in the required manifest at `.codex-plugin/plugin.json`.

## Policy

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Bump `PATCH` for docs, cleanup, and non-behavioral fixes
- Bump `MINOR` for new skills, hooks, or workflows that stay backwards compatible
- Bump `MAJOR` for breaking manifest, hook, or workflow changes

## Why it matters

Codex installs plugins by marketplace source and plugin version. The version in the manifest is the release identifier Codex uses when it resolves and caches a plugin install.

## What to change for a release

1. Update `plugins/ace-codex/.codex-plugin/plugin.json`
2. Update `CHANGELOG.md`
3. Re-run the test suite
4. Commit the release bump together with the code or docs change that caused it
