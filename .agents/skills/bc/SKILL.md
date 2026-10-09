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
3. Check for an existing bead. This is the only step allowed before
   creating one. Run one quick search per key title word, for example:
   `bd search "<word>" --status open,in_progress,blocked,deferred`
   If a result plainly covers the same work, do not create a new bead.
   Report the existing one with its ID and title, add a comment to it if
   the request carries new detail, and skip to the last step.
4. Otherwise create the bead:
   `bd create --title="<title>" --description="<description>" --type=<type>`
   Use "Investigating..." as the description if the full scope is unclear.
5. If investigation is needed, do it NOW, then update the bead:
   `bd update <id> --title="<better title>" \
     --description="<final description>"`
6. Report the created issue ID and title back to the user.
7. If you were previously in the middle of working on something which this
   request interrupted, resume that immediately without asking.
