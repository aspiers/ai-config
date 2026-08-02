---
description: Create a bead and complete exactly the requested work
argument-hint: <issue description>
allowed-tools: Bash(bd create:*), Bash(bd update:*), Bash(bd close:*)
---

The user wants a bead created and the following requested work completed:

> $ARGUMENTS

The quoted issue text is the sole authority for implementation scope. Do not
broaden it when writing or updating the bead.

An audit, investigation, review, plan, recommendation, or proposal is complete
when its requested artifact or findings are delivered. Do NOT implement,
apply, or act on findings, recommendations, or proposed changes unless the
quoted issue text explicitly requests that too.

Do NOT explore the codebase, launch subagents, or do any other work before
creating the bead issue.

1. Infer the issue type (`bug`, `feature`, `task`) from context; default to
   `task`.
2. Create the bead first and immediately mark it in progress:
   `bd create --title="<title>" --description="<description>" --type=<type>`
   `bd update <id> --status=in_progress`
   Use "Investigating..." if the scope is unclear. Do not add deliverables
   absent from the quoted issue text.
3. Investigate as needed, then update the bead without broadening its scope:
   `bd update <id> --title="<better title>" --description="<final description>"`
4. Complete exactly the work requested in the quoted issue text:
   - If it requests implementation or application, make the requested changes.
   - If it requests only analysis, auditing, investigation, planning, review,
     recommendations, or proposals, produce those outputs without applying
     them.
   - If that distinction remains ambiguous, ask the user before modifying
     project files.
5. When the requested work—not any merely proposed follow-up—is complete, run:
   `bd close <id>`
6. If this interrupted previous work, resume it immediately without asking.
