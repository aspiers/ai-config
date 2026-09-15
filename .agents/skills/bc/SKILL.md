---
name: bc
description: >-
  Creates a Beads issue for a described problem or piece of work without
  doing the work itself. Use when the user invokes `/bc` or `$bc`, or asks to
  file, log, or record a bead for something. To also carry out the work, use
  the `bx` skill instead.
---

# Create a bead for the described issue

Do NOT explore the codebase, launch subagents, or do any other work before
creating the bead issue.

1. Load the `beads-best-practices` skill and follow it when writing the bead.
2. Infer the issue type (`bug`, `feature`, `task`) from context; default to
   `task`.
3. ALWAYS create the bead FIRST:
   `bd create --title="<title>" --description="<description>" --type=<type>`
   Use "Investigating..." as the description if the full scope is unclear.
4. If investigation is needed, do it NOW, then update the bead:
   `bd update <id> --title="<better title>" \
     --description="<final description>"`
5. Report the created issue ID and title back to the user.
6. If you were previously in the middle of working on something which this
   request interrupted, resume that immediately without asking.
