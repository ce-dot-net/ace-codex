# Privacy Policy

`ace-codex` is a Codex marketplace plugin that orchestrates local `ace-cli` workflows.

## What the plugin stores locally

- Workspace binding in `.codex/ace.json`
- Session-scoped ACE runtime state in `.codex/.ace-codex/sessions/<session_id>/`
- Workspace-scoped domain state in `.codex/.ace-codex/workspace/`

This local state may include prompts, tool activity metadata, review prompts, review results, and ACE retrieval metadata needed to power retrieval, learning, and review workflows.

## What the plugin sends to ACE

When configured and used, the plugin invokes the installed `ace-cli`. That may send data to ACE services, including:

- workspace binding identifiers such as `org_id` and `project_id`
- retrieval queries
- learning traces derived from tool usage
- bootstrap, status, and review-related requests

The exact server-side handling for ACE data is determined by the ACE platform and `ace-cli`, not by this repository alone.

## Authentication

- Codex plugin configuration is local to the user
- ACE authentication is handled by `ace-cli`
- ACE auth state is stored in `~/.config/ace/config.json`

The plugin does not embed credentials in this repository and does not require committing secrets into the workspace.

## User control

Users can:

- remove `.codex/ace.json`
- remove `.codex/.ace-codex/`
- uninstall the plugin from Codex
- log out of ACE through `ace-cli`

## Contact

For repository issues, open an issue in this repository.
