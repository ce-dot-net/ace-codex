---
name: ace-export-patterns
description: Use when the user wants to export the current ACE playbook to a local JSON file for backup, sharing, or migration to another project.
---

Invoke directly with `$ace-export-patterns`, or ask `@ace-codex` to back up the playbook.

Run `ace-cli export --output <path>`. If `--output` is omitted, the JSON is written to stdout.

Suggest a default path under the repo such as `./ace-playbook-export-$(date +%Y%m%d).json` so the file is not lost in the home directory. Confirm the file size and pattern count after export.
