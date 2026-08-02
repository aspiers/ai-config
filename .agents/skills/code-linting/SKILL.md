---
name: code-linting
description: Discover and run the linters and format checks relevant to changed code. Use after code edits or when the user asks for lint, formatting, or static-analysis validation.
---

# Code Linting

Use the repository's own quality gates and scope them to the change when that
provides reliable coverage.

## Workflow

1. Read applicable agent instructions and project documentation, then inspect
   build configuration for the authoritative lint commands.
2. Select checks relevant to the changed languages and files. Prefer a
   repository-provided aggregate command when it is clearly intended as the
   gate.
3. Determine whether a command mutates files. Run check mode first unless the
   user or repository workflow authorizes automatic fixes.
4. Run the checks and fix findings caused by the current work when feasible.
5. Re-run affected checks after edits and report exact commands and outcomes.

Do not guess a command from language alone when project configuration provides
a different interface. If no lint workflow exists, state what you inspected
and use judgement about whether a standard tool can be run safely.

## Interpret results

Distinguish:

- findings introduced by the current change;
- pre-existing findings outside the changed scope;
- tool or environment failures; and
- warnings that are intentionally permitted by project policy.

Do not claim success when the command failed or covered only part of the
requested scope. Do not silently broaden the task to repair unrelated legacy
findings; report them and follow repository or user guidance on whether they
block completion.
