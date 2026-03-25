---
name: plan-to-beads
description: Decompose an approved implementation plan into self-contained beads issues with zero guesswork. Use when breaking down a plan file into actionable beads tasks.
---

# Plan to Beads

You are taking an approved implementation plan and decomposing it into beads
(bd) issues. Each bead must be **100% self-contained** so that any agent
picking it up has zero questions and needs zero assumptions. However it should
also reference the plan file(s) and other relevant resources it was based on.

## Workflow

### 1. Find the plan

If the user provided a specific file as an argument, use that. Otherwise use
the most recently referenced plan in the existing conversation. If no such
plan exists, ask the user to provide one.

Read the plan thoroughly before proceeding.

### 2. Explore the codebase if needed

Before proposing beads, check how detailed the plan is in terms of:

- The files that will be modified
- Existing patterns, functions, and utilities that should be reused
- The current state of code related to the plan
- Test patterns used in similar features

If these are already established in the plan, then they should be used directly.

Otherwise, explore the codebase to discover them.  This detail is critical —
beads need concrete file paths and function references, not vague
descriptions.

### 3. Propose Beads

Break the plan into granular implementation tasks. For each proposed bead, show:

```
[1] <title>
    Depends on: (none | bead numbers)
    Files: <file paths>
    Summary: <2-3 sentences>

[2] <title>
    Depends on: [1]
    Files: <file paths>
    Summary: <2-3 sentences>
```

### 4. Refine with User

Present the proposed beads and ask for feedback if anything is not clear:

- Should any beads be split further?
- Should any be merged?
- Are dependencies correct?
- Missing anything?

Iterate until the user approves.

### 5. Choose a Feature Label

Before creating beads, choose a short, kebab-case label (e.g., `fiscal-host`,
`project-collections`) that will be applied to every bead in this set.

**The label MUST be new.** Verify it doesn't already exist:

```bash
bd list --label <feature-slug>
```

If any results are returned, choose a different label (e.g., append a version:
`fiscal-host-v2`). Reusing an existing label would mix unrelated beads
together.

### 6. Create Beads

For each approved bead, create it using `--body-file -` to pipe the multi-line
description. **Every bead must** carry the feature label.

**Do NOT heredoc into `bd create` directly — it does not read stdin without `--body-file -`.**

```bash
cat << 'BEAD_EOF' | bd create "Bead title" --type task --priority 2 --labels <feature-slug> --body-file -
## Context
...

## Task
...

## Files
...

## Acceptance Criteria
...
BEAD_EOF
```

Then set dependencies with `bd dep add`.

## Bead Quality Standard

**Every bead MUST follow these rules. No exceptions.**

### 100% Self-contained

A bead includes ALL context an agent needs to complete the work without
reading the plan, without asking questions, and without exploring the codebase
to figure out what to do. The bead IS the spec for that task.

### References relevant context

The bead should reference the plan file(s) and other relevant resources it was
based on or needs.

### No assumptions

Bad: "Update the service to handle the new field"

Good: "In `src/services/user/UserService.ts`, add a `displayName` parameter
(type: `string`, max 50 chars) to the `updateProfile` method.""

### No guesswork

Bad: "Add validation for the input"

Good: "In `src/routes/api/user.ts`, add validation to the request body using
the existing `userUpdateSchema` from `src/lib/schemas/user.ts`.  On validation
failure, return HTTP 400 with a structured error response using the project's
error helper. Test: send a request with `displayName` exceeding 50 chars and
verify 400 response."

### Clear dependencies

Bad: "This needs the database migration to be done first"

Good: "Depends on bead `proj-abc123` (Add display_name column to users
table). This bead expects the `display_name` column (type: `varchar(50)`,
nullable, default null) to exist on the `users` table."

### Acceptance criteria

Bad: "Implement the feature"

Good: "Done when: (1) POST /api/user with `{ displayName: 'Test' }` updates
the `display_name` column in the database, (2) GET /api/user returns the
`displayName` field in the response, (3) Sending `displayName` longer than 50
chars returns HTTP 400, (4) Unit test covers all three cases and passes,
(5) All changes committed to git as logically grouped commit(s)."

### Scoped to one concern

If a bead touches multiple files for different reasons, split it.  A schema
migration is one bead.  The service change is another.  The API route change
is another.  The tests are another (or colocated with the service bead if
tightly coupled).

## Bead Description Template

Every bead description MUST follow this structure:

```
## Context

[Why this task exists. Reference the broader goal and any relevant issue IDs and resources.]

## Task

[Exactly what to do. Specific files, functions, line numbers where known, exact changes.]

## Files

[Every file path that will be read or modified, with what happens to each:]
- `src/path/to/file.ts` — modify: add X method
- `src/path/to/other.ts` — read: reference existing Y pattern
- `test/path/to/file.test.ts` — create: tests for X

## Dependencies

[What must be complete before this. What this produces for downstream beads:]
- Depends on: <bead-id> (<title>) — needs <specific thing>
- Produces: <what downstream beads will consume>

## Acceptance Criteria

[Concrete, testable conditions. Not "implement X" but "when Y happens, Z results":]
1. <specific testable condition>
2. <specific testable condition>
3. <specific testable condition>
4. All changes committed to git as logically grouped commit(s)
```

## Rules

- **NEVER create vague beads** — if you can't fill in the template with specifics, you haven't explored the codebase enough
- **ALWAYS include relevant issue references** in each bead's Context section when available
- **ALWAYS include the plan file path** in each bead's Context section for traceability
- Use `bd create --type task --priority 2 --labels <feature-slug>` as the default. Adjust priority based on dependency order (earlier = higher priority)
- **NEVER use `--parent` or create epic parent beads** — use labels for grouping and `bd dep add` for ordering
- **ALWAYS apply a consistent, unique label** (short kebab-case feature name) to every bead in the set
- **Every bead MUST have at least one label** — beads without labels are rejected
- After creating all beads, show a summary with bead IDs, titles, labels, and dependency graph
