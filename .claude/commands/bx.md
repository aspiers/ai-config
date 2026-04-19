---
description: Create a new bead and immediately implement it
argument-hint: <issue description>
allowed-tools: Bash(bd create:*), Bash(bd update:*), Bash(bd close:*)
---

The user wants a bead created and implemented for the following issue:

> $ARGUMENTS

Do NOT explore the codebase, launch subagents, or do any other work
before creating the bead issue.

1. Infer the issue type (`bug`, `feature`, `task`) from context; default to `task`.
2. ALWAYS create the bead FIRST and immediately mark it in progress:
   `bd create --title="<title>" --description="<description>" --type=<type>`
   `bd update <id> --status=in_progress`
   Use "Investigating..." as the description if the full scope is unclear.
3. If investigation is needed, do it NOW, then update the bead:
   `bd update <id> --title="<better title>" --description="<final description>"`
4. Implement the work described in the issue.
5. After implementation is complete, run: `bd close <id>`
6. If you were previously in the middle of working on something which this request interrupted, resume that immediately without asking.
