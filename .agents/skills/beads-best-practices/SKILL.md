---
name: beads-best-practices
description: >-
  Applies reusable Beads writing and update practices in every context. Use
  whenever reading, creating, updating, commenting on, closing, superseding,
  or handing off Beads issues, including alongside beads, beads-solo, and
  plan-to-beads workflows.
---

# Beads Best Practices

Apply these practices to every Beads interaction, regardless of repository,
storage mode, team policy, or higher-level workflow.

When the repository opts into the solo-maintainer policy, also load and follow
[`beads-solo`](../beads-solo/SKILL.md). That skill controls authorization,
setup, storage, and governance; this skill controls reusable issue-writing and
update practices. Neither supersedes the other.

## Claim Before Starting Work

Inspect the bead, then claim it before beginning substantive work:

```bash
bd show "$id"
bd update "$id" --claim
```

Do not edit code, change project state, or begin the task while its bead
remains unclaimed. Claiming makes ownership visible and prevents duplicated
work.

If another worker already owns the bead, do not overwrite the assignee or work
on it in parallel without coordination. Stop and resolve ownership through the
active project workflow. Re-running `--claim` is acceptable when the bead is
already assigned to the current worker.

## Keep Work-in-Progress Status Honest

Treat `in_progress` as evidence of work happening now, not as a reservation for
a batch of issues you intend to address later. By default, claim exactly one
bead at a time and leave related or queued work `open` while you inspect or
sequence it.

Before switching to another bead:

1. Close the current bead if its acceptance criteria are complete; or
2. Post a checkpoint comment and return it to `open` (or defer it) if work is
   pausing.
3. Then inspect and claim the next bead immediately before starting it.

Multiple beads may be `in_progress` only when work is genuinely concurrent,
such as separate workers actively owning independent tasks, or when the active
workflow explicitly requires overlapping tracked work. Do not bulk-claim a
label, epic, milestone, search result, or requested task set merely because all
items are in scope.

## Pair IDs with Human-Readable Titles

Never refer to a bead in human-facing prose solely by its opaque ID. Pair the
ID with its title or a concise human-readable description so readers do not
have to look it up to understand the reference.

Prefer either of these forms:

```markdown
- `ai-wt0` — **Handle expired sessions**
- Handle expired sessions (`ai-wt0`)
```

Apply this to conversation responses, progress reports, comments, handoffs,
blocker explanations, commit summaries, and lists of related work. When a bead
has already been introduced in the immediate context, use its readable title
rather than falling back to the bare ID. Bare IDs remain appropriate in
machine-facing commands such as `bd show ai-wt0`.

## Track Every Work Item

All substantive project work must be represented by a bead. Do not perform
untracked work merely because it is small, related to the active task, or a
tangent discovered along the way.

When a distinct work item emerges during another task:

1. Create a new bead before pursuing it.
2. Explain the discovery and the work clearly in its Markdown body.
3. Link it to the active bead, normally with `discovered-from`:

   ```bash
   bd create --title="Newly discovered work" \
       --deps="discovered-from:$active_id" --body-file - <<'EOF'
   ## Context

   Discovered while working on the originating bead.

   ## Task

   Describe the distinct follow-up work.
   EOF
   ```

4. Add blocking dependencies when the new work must finish before the active
   bead can continue.
5. Return to the active bead, or explicitly claim the new bead before
   switching to it.

Create the bead even when the work will be deferred or handed to someone else.
Do not silently expand the active bead's scope. Routine steps already required
by its stated task and acceptance criteria remain in that bead and do not need
separate per-command issues.

## Choose Grouping Deliberately

Labels and epics are different mechanisms, and they compose. Applying a label
to every bead in a set is nearly always right; adding an epic parent is a
separate decision.

Use a **label** for an attribute or a perpetual category with no end state,
such as `area:auth`, `tech-debt`, or `needs-review`. A bead can carry several,
they cross-cut unrelated work, and they can be applied retroactively without
restructuring anything.

Use an **epic** for a bounded deliverable with a done condition. An epic is a
real issue, so it carries status, priority, and a description holding the
feature-level narrative and acceptance criteria; it reports roll-up progress
through `bd epic status`; and it can itself block or be blocked. In exchange
it is an extra issue to maintain and close, and each bead has only one parent.

An epic whose done condition never arrives is worse than no epic. When a set
of work has no feature-level completion state, group it with a label alone.

### Hierarchy Is Not Dependency

`--parent` records presentational hierarchy only. It imposes no ordering
whatsoever.

The value of Beads is an arbitrary dependency graph, so never let a parent
tree stand in for it. Record every real ordering constraint explicitly with
`bd dep add`, including dependencies between children of the same epic, which
may depend on one another in any shape the work requires.

Note also that epics appear in `bd ready` alongside actionable work. Filter
them out with `bd ready --exclude-type=epic` when that is noisy.

## Reference the Bead in Every Commit

When a commit implements, advances, or closes tracked work, name the bead in
its message. A commit that leaves no trace of its bead forces readers to
reconstruct the link from timestamps, and the rationale recorded in the bead
becomes unreachable from the code history.

Use the trailer form unless the repository already uses another convention:

```
Refs: bead ai-wt0
```

Determine the convention from the repository rather than assuming, and prefer
an explicit documented rule over inference:

1. Check the project's agent instructions for a stated commit convention.
2. Otherwise search the history for existing references, rather than reading
   only the last handful of commits:

   ```bash
   git log --format='%h|%s|%b' | grep -iE '\b(refs|closes|fixes)\b.*[a-z]+-[a-z0-9]+' | head
   ```

Sampling only recent commits is unreliable: a convention applied
inconsistently, or omitted from the most recent work, will look absent. Treat a
single documented or historical example as establishing the convention, and
raise the inconsistency rather than silently following the omission.

When no convention exists anywhere, add the `Refs:` trailer and say so, so the
maintainer can confirm or correct it.

## Write Human-facing Content as Markdown

Treat every human-facing text field as Markdown:

- descriptions and bodies
- design and acceptance criteria
- notes, when their use is appropriate
- comments
- close or supersede reasons
- handoff and blocker updates

Use headings, paragraphs, lists, checkboxes, inline code, fenced code blocks,
and links where they make the content easier to scan.

Avoid walls of text. Separate sections and paragraphs with blank lines, and
turn sequences or sets of facts into lists. Do not rely on renderer word wrap
or single newlines inside one paragraph to provide structure.

Keep titles concise plain text; put detail in the Markdown body.

### Link Every Relevant Reference

Represent GitHub issues, pull requests, documentation, dashboards, and other
relevant web references as descriptive Markdown hyperlinks. Do not leave a
bare URL or an unlinked textual reference when its target is available.

Use direct links and labels that identify the destination. Format technical
identifiers inside link labels as inline code:

```markdown
- Issue: [`owner/repository#123`][issue]
- Pull request: [`owner/repository#456`][pull-request]
- Reference: [Beads sync concepts][sync-concepts]

[issue]: https://github.com/owner/repository/issues/123
[pull-request]: https://github.com/owner/repository/pull/456
[sync-concepts]: https://example.com/beads/sync-concepts
```

Resolve the canonical target before posting. Do not fabricate a URL when the
link target is unknown; find it first, or state clearly that it could not be
resolved.

### Format Technical Text as Code

Enclose code, technical symbols, and identifiers in backticks. This includes:

- function, class, method, variable, and type names;
- file and directory paths;
- commands, subcommands, arguments, and flags;
- environment variables and configuration keys;
- package names, versions, branches, tags, and commit identifiers;
- Beads IDs and other issue identifiers; and
- API routes, HTTP methods, field names, and literal values.

Use inline code for short items such as `bd update`, `--claim`,
`src/auth/session.ts`, `refreshToken`, and `ai-wt0`. Use a fenced code block
with an appropriate language for multiline commands, code, structured data,
or logs. Do not use backticks merely for emphasis around ordinary prose.

## Preserve Real Line Breaks

Pass actual newline characters to `bd`. Do not store literal `\n` sequences,
and do not compress structured content into a long one-line flag value.

Prefer stdin or file flags when the command supports them:

```bash
bd create --title="Handle expired sessions" --type=task --body-file - <<'EOF'
## Context

Expired sessions currently produce an unclear error.

## Acceptance Criteria

- Return an actionable message.
- Cover the expired-session path with a test.
EOF
```

```bash
bd update "$id" --body-file - <<'EOF'
## Context

The failure occurs before token refresh.

## Next Step

Add coverage around the refresh boundary.
EOF
```

For a multiline comment, preserve the Markdown in a shell variable or file:

```bash
comment=$(cat <<'EOF'
## Progress

- Added the regression test.
- Confirmed that it fails before the fix.

## Next Step

Update the refresh path.
EOF
)
bd comments add "$id" "$comment"
```

Use the same pattern for fields that only accept string flags. Quote every
multiline variable expansion.

## Use Comments for Chronological Updates

Append a comment rather than updating `notes` whenever time, author, order, or
history is relevant. Comments are the durable activity log and preserve the
metadata needed to understand how work evolved.

Use comments for:

- progress and handoff updates
- discoveries and investigation results
- decisions and their rationale
- blockers and unblock events
- test or review results
- changes in approach or scope

Keep every active bead regularly updated. Post a comment at meaningful
checkpoints rather than waiting until the task is complete. At minimum,
comment:

- after substantial progress or a significant discovery or decision;
- whenever the blocker, scope, approach, or next step changes; and
- before pausing, handing off, or ending a work session.

For long-running work, add periodic checkpoint comments even when no major
milestone has completed, so the latest comment still explains the current
state and next step. Do not comment after every command or create noise; the
cadence should make the work resumable by another person or agent.

Do not append a running journal to `notes`. The notes field is not
timestamped.
Reserve it, if used at all, for timeless supplementary information that
represents the issue's current state and is safe to replace as a whole. When
in doubt, post a comment.

## Keep Updates Useful

- State what changed, why it matters, and what happens next.
- Reference relevant issue IDs, commits, files, commands, or URLs.
- Use concrete outcomes instead of vague status such as "made progress."
- Keep each update focused; use multiple paragraphs or sections when it covers
  distinct facts.
- Never include credentials, private data, or unrelated environment details.
