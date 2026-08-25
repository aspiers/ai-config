---
description: Create a bead and complete exactly the requested work
argument-hint: <issue description>
---

The user wants a bead created and the following requested work completed:

> $ARGUMENTS

The quoted issue text is the sole authority for implementation scope. Do not
broaden it when writing or updating the bead.

An audit, investigation, review, plan, recommendation, or proposal is complete
when its requested artifact or findings are delivered. Do NOT implement,
apply, or act on findings, recommendations, or proposed changes unless the
quoted issue text explicitly requests that too.

Do NOT explore the codebase, delegate to another workflow, or do any other work
before creating the bead issue.

1. Load the `beads-best-practices` skill and follow it when writing any bead.
   In particular, a bead is done by a person or by an agent, never by both:
   split out anything needing a human decision, approval, credential, or
   observation into its own `human`-labelled bead joined by a dependency.
   This applies to every bead you create here, including incidental ones for
   follow-up work you noticed along the way.
2. Infer the issue type (`bug`, `feature`, `task`) from context; default to
   `task`.
3. Create the bead first and immediately mark it in progress:
   `bd create --title="<title>" --description="<description>" --type=<type>`
   `bd update <id> --status=in_progress`
   Use "Investigating..." if the scope is unclear. Do not add deliverables
   absent from the quoted issue text.
4. Investigate as needed, then update the bead without broadening its scope:
   `bd update <id> --title="<better title>" --description="<final description>"`
5. Complete exactly the work requested in the quoted issue text:
   - If it requests implementation or application, make the requested changes.
   - If it requests only analysis, auditing, investigation, planning, review,
     recommendations, or proposals, produce those outputs without applying
     them.
   - If that distinction remains ambiguous, ask the user before modifying
     project files.
6. When the requested work—not any merely proposed follow-up—is complete, run:
   `bd close <id>`
7. If this interrupted previous work, resume it immediately without asking.
