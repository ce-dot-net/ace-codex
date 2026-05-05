# Support

Use this repository as the source for the `ace-codex` Codex marketplace plugin.

## If installation fails

1. Verify `codex` is installed and up to date.
2. Add the repo as a marketplace source:

   ```bash
   codex plugin marketplace add .
   ```

3. Open `/plugins` in Codex and install `ace-codex`.
4. Confirm `ace-cli` is installed and authenticated.
5. Bind the workspace with a valid ACE org/project in `.codex/ace.json`.

## If runtime commands fail

- Run `./plugins/ace-codex/scripts/ace-doctor.sh`.
- Run `./plugins/ace-codex/scripts/ace-status.sh .`.
- Recheck the local ACE project binding and your ACE backend access.
- If review or learn state looks missing, inspect `.codex/.ace-codex/sessions/<session_id>/` for the active Codex session and `.codex/.ace-codex/workspace/` for shared domain state.

## Where to report issues

- Open an issue in this repository.
- Include the output of `ace-doctor` and `ace-status`.
- Include your `ace-cli` version and Codex version.
