---
name: ace-install-cli
description: Use when the user does not have `ace-cli` on their PATH and needs to install or upgrade it before any other ACE skill can run. Installs the published ACE CLI from npm.
---

Invoke directly with `$ace-install-cli`, or ask `@ace-codex` to install `ace-cli`.

Workflow:
1. Check whether `ace-cli` is already on PATH with `command -v ace-cli`. If found, print the version with `ace-cli --version` and stop.
2. Confirm `npm` is available with `command -v npm`. If not, tell the user to install Node.js (LTS) first and stop.
3. Install or upgrade with:

   ```bash
   npm install -g @ace-sdk/cli
   ```

4. Verify the install with `ace-cli --version`.
5. Tell the user to run `$ace-login` next.

Do not assume sudo. If npm install fails with a permission error, suggest the user fix npm's prefix (`npm config set prefix ~/.npm-global`) or use a Node version manager.
