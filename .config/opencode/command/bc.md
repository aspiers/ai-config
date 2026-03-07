---
description: Create a new bead for the described issue
---

The user wants a bead created for the following issue:

> $ARGUMENTS

Do NOT explore the codebase, launch subagents, or do any other work
before creating the bead issue.

1. Infer the issue type (`bug`, `feature`, `task`) from context; default to `task`.
2. ALWAYS create the bead FIRST:
   `bd create --title="<title>" --description="<description>" --type=<type> --json`
   Use "Investigating..." as the description if the full scope is unclear.
3. If investigation is needed, do it NOW, then update the bead:
   `bd update <id> --title="<better title>" --description="<final description>" --json`
4. Report the created issue ID back to the user.
5. If you were previously in the middle of working on something which this request interrupted, resume that immediately without asking.
