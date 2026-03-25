---
name: plan-to-linear
description: Decompose an approved implementation plan into self-contained Linear issues with zero guesswork. Use when breaking down a plan into actionable Linear tasks via the MCP server.
---

# Plan to Linear

You are taking an approved implementation plan and decomposing it into Linear
issues via the Linear MCP server. Each issue must be **100% self-contained**
so that any agent picking it up has zero questions and needs zero assumptions.
It should also reference the plan and other relevant resources it was based
on.

## Prerequisites

The Linear MCP server must be configured. If it is not available, tell the
user to set it up.

**Claude Code:**

```
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

Then run `/mcp` to authenticate.

**OpenCode** — add to `opencode.json` (project or global):

```json
{
  "mcp": {
    "linear": {
      "type": "remote",
      "url": "https://mcp.linear.app/mcp"
    }
  }
}
```

Then run `opencode mcp auth linear` to authenticate.

## Workflow

### 1. Find the plan

The plan may be provided as:

- A **file path** (the user passes it as an argument or references it in
  conversation)
- A **Linear issue** (the plan is stored in the description of a parent issue
  — use `get_issue` to retrieve it)

If neither is provided, check the existing conversation for a recently
referenced plan. If none exists, ask the user to provide one.

Read the plan thoroughly before proceeding.

### 2. Discover the Linear workspace

Before creating issues, gather workspace context:

- Use `list_teams` to find available teams
- Ask the user which team to create issues under (or confirm if obvious)
- Use `list_issue_labels` (with the team) to see existing labels
- Use `list_issue_statuses` (with the team) to understand the workflow states
- Use `list_projects` to see if there's a relevant project to associate with

### 3. Explore the codebase if needed

Before proposing issues, check how detailed the plan is in terms of:

- The files that will be modified
- Existing patterns, functions, and utilities that should be reused
- The current state of code related to the plan
- Test patterns used in similar features

If these are already established in the plan, then they should be used directly.

Otherwise, explore the codebase to discover them. This detail is critical —
issues need concrete file paths and function references, not vague
descriptions.

### 4. Propose Issues

Break the plan into granular implementation tasks. For each proposed issue,
show:

```
[1] <title>
    Parent: (none | issue number — for sub-issue grouping)
    Blocked by: (none | issue numbers)
    Files: <file paths>
    Summary: <2-3 sentences>

[2] <title>
    Parent: [1]
    Blocked by: (none)
    Files: <file paths>
    Summary: <2-3 sentences>
```

#### Structuring with Sub-issues

Use **sub-issues** (parent/child) for logical grouping — when several issues
are parts of one coherent unit of work. The parent issue describes the overall
goal; children are the individual implementation steps.

For example, a "User profile display name" feature might have a parent issue
with children for schema migration, service layer, API route, and tests.

Use **blocking relations** (`blocks`/`blockedBy`) for ordering — when one
issue must complete before another can start, regardless of whether they share
a parent.

These are orthogonal: sub-issues within the same parent can block each other
(e.g., migration child blocks service-layer child), and blocking can cross
parent boundaries.

### 5. Refine with User

Present the proposed issues and ask for feedback:

- Should any issues be split further?
- Should any be merged?
- Are dependencies and parent groupings correct?
- Missing anything?

Iterate until the user approves.

### 6. Decide on Organisation

Issues need to be grouped so they can be found and filtered together. Linear
offers several mechanisms; the right choice depends on the workspace's
conventions and the scope of the work.

**Consider the following options (not mutually exclusive):**

- **Project** — most common for a feature or initiative spanning multiple
  issues. Use `list_projects` to see if a suitable project already exists, or
  create one with `save_project`.
- **Milestone** — if the project uses milestones to track phases, assign all
  issues to the appropriate milestone via `save_issue(milestone: ...)`.
- **Label** — useful as a lightweight tag, especially for cross-cutting
  concerns or when a project would be overkill. Prefer reusing existing
  labels (from `list_issue_labels`) in a manner consistent with how other
  issues in the workspace use them. Only create a new label with
  `create_issue_label` if no suitable one exists.
- **Sub-issue grouping alone** — if all issues share a single parent issue,
  that may provide sufficient organisation without any of the above.

**If the right approach is obvious** (e.g., the plan names a project, or the
user has already specified one), use it directly.

**Otherwise, ask the user** which organisation strategy to use, presenting the
options above with a brief explanation. Do not assume.

### 7. Create Issues

Create issues using the `save_issue` MCP tool. The creation order matters
because you need IDs from parent issues and blocking issues before you can
reference them.

**Creation order:**

1. **Parent issues first** (if using sub-issue grouping)
2. **Blocking issues before the issues they block**
3. **Leaf issues last**

For each issue, call `save_issue` with:

```
save_issue(
  title: "Issue title",
  team: "<team-name-or-id>",
  description: "<full markdown description — see template below>",
  priority: 3,           # 1=Urgent, 2=High, 3=Normal, 4=Low
  parentId: "<parent-id>",    # if this is a sub-issue
  blockedBy: ["<issue-id>"],  # issues that must complete first
  project: "<project-name>",  # if using a project
  milestone: "<milestone>",   # if using milestones
  labels: ["<label>"],        # if using labels
)
```

**Setting blocking relations:**

- `blockedBy: ["LIN-123"]` — this issue is blocked by LIN-123
- `blocks: ["LIN-456"]` — this issue blocks LIN-456

Use whichever direction is natural at creation time. Both fields are
append-only (existing relations are never removed).

After creating all issues, show a summary with issue identifiers, titles,
parent relationships, and the dependency graph.

## Issue Quality Standard

**Every issue MUST follow these rules. No exceptions.**

### 100% Self-contained

An issue includes ALL context an agent needs to complete the work without
reading the plan, without asking questions, and without exploring the codebase
to figure out what to do. The issue IS the spec for that task.

### References relevant context

The issue should reference the plan file(s) and other relevant resources it
was based on or needs.

### No assumptions

Bad: "Update the service to handle the new field"

Good: "In `src/services/user/UserService.ts`, add a `displayName` parameter
(type: `string`, max 50 chars) to the `updateProfile` method."

### No guesswork

Bad: "Add validation for the input"

Good: "In `src/routes/api/user.ts`, add validation to the request body using
the existing `userUpdateSchema` from `src/lib/schemas/user.ts`. On validation
failure, return HTTP 400 with a structured error response using the project's
error helper. Test: send a request with `displayName` exceeding 50 chars and
verify 400 response."

### Clear dependencies

Bad: "This needs the database migration to be done first"

Good: "Blocked by LIN-123 (Add display_name column to users table). This
issue expects the `display_name` column (type: `varchar(50)`, nullable,
default null) to exist on the `users` table."

### Acceptance criteria

Bad: "Implement the feature"

Good: "Done when: (1) POST /api/user with `{ displayName: 'Test' }` updates
the `display_name` column in the database, (2) GET /api/user returns the
`displayName` field in the response, (3) Sending `displayName` longer than 50
chars returns HTTP 400, (4) Unit test covers all three cases and passes,
(5) All changes committed to git as logically grouped commit(s)."

### Scoped to one concern

If an issue touches multiple files for different reasons, split it. A schema
migration is one issue. The service change is another. The API route change is
another. The tests are another (or colocated with the service issue if tightly
coupled).

## Issue Description Template

Every issue description MUST follow this structure:

```markdown
## Context

[Why this task exists. Reference the broader goal, plan file path, and any relevant issue IDs and resources.]

## Task

[Exactly what to do. Specific files, functions, line numbers where known, exact changes.]

## Files

[Every file path that will be read or modified, with what happens to each:]
- `src/path/to/file.ts` — modify: add X method
- `src/path/to/other.ts` — read: reference existing Y pattern
- `test/path/to/file.test.ts` — create: tests for X

## Dependencies

[What must be complete before this. What this produces for downstream issues:]
- Blocked by: LIN-123 (<title>) — needs <specific thing>
- Produces: <what downstream issues will consume>

## Acceptance Criteria

[Concrete, testable conditions. Not "implement X" but "when Y happens, Z results":]
1. <specific testable condition>
2. <specific testable condition>
3. <specific testable condition>
4. All changes committed to git as logically grouped commit(s)
```

## Rules

- **NEVER create vague issues** — if you can't fill in the template with specifics, you haven't explored the codebase enough
- **ALWAYS include relevant issue references** in each issue's Context section when available
- **ALWAYS include the plan file path** in each issue's Context section for traceability
- Use priority 3 (Normal) as the default. Adjust based on dependency order (earlier = higher priority)
- **Use sub-issues for grouping** related implementation steps under a parent that describes the overall goal
- **Use `blocks`/`blockedBy` for ordering** — when one issue must complete before another can start
- **ALWAYS organise issues consistently** — use whichever combination of project, milestone, label, or sub-issue grouping was agreed with the user, and apply it to every issue in the set
- **Create parent issues before children** — you need the parent ID to set `parentId`
- **Create blocking issues before blocked ones** — you need the blocker ID to set `blockedBy`
- After creating all issues, show a summary with issue identifiers, titles, parent/child relationships, and dependency graph
