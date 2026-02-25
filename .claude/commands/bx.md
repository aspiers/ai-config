---
description: Create a new bead and immediately implement it
argument-hint: <issue description>
allowed-tools: Bash(bd create:*), Bash(bd update:*), Bash(bd close:*)
---

Create a new bead issue and implement it immediately.

1. Parse the user's input to determine an appropriate short title and description.
2. Infer the issue type (`bug`, `feature`, `task`) from context; default to `task`.
3. Run: `bd create --title="<title>" --description="<description>" --type=<type> --json`
4. Run: `bd update <id> --status=in_progress --json`
5. Implement the work described in the issue.
6. After implementation is complete, run: `bd close <id> --json`
