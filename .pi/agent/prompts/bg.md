---
description: "Grind through beads in priority order non-stop"
argument-hint: "<optional scope - label / epic ID / priority / type>"
---

Work through beads continuously in priority order. DO NOT STOP between issues.
Apply the `beads-best-practices` skill throughout, especially its human-attention
and honest work-in-progress rules.

## Scope

> $ARGUMENTS

If the above is empty, work through every ready bead.

Otherwise treat it as a restriction on which beads to work on, and translate
it into filter flags for `bd ready`:

| Requested scope | Flag |
| --- | --- |
| A label | `--label=<label>` (repeat to require all; `--label-any` for any) |
| Beads within an epic | `--parent=<epic-id>` (matches all descendants) |
| A priority | `--priority=<0-4>` |
| An issue type | `--type=<bug\|feature\|task\|chore>` |
| An assignee | `--assignee=<name>` |

A bare word with no other context means a label, so `/bg fiscal-host` becomes
`bd ready --label=fiscal-host`. Combine flags when the scope names more than
one restriction.

**The scope is authoritative.** Apply it to every `bd ready` call for the
whole run. Never widen it, and never fall back to the unfiltered queue.

If the scope is ambiguous, or names a label or epic that matches nothing, ask
the user rather than guessing. Verify an epic ID exists with `bd show <id>`
before using `--parent`.

## Workflow

Loop forever:

1. Run `bd ready --exclude-label=human` with the scope flags to get the list of
   agent-ready (unblocked) issues.
2. Look at the top 5 highest-priority issues from the output. Do NOT
   spend time analysing beyond these 5. Pick whichever one you can
   make the most immediate progress on.
3. Mark it in progress: `bd update <id> --status=in_progress`
4. Show issue details: `bd show <id>`
5. Implement the work. Follow normal development practices (tests,
   linting, commits) but stay focused and move fast.
6. When done, close it: `bd close <id>`
7. Commit your changes, and push them unless the repository's own rules say
   otherwise (see **Pushing** below).
8. **Go immediately to step 1.** Do NOT pause, do NOT ask the user
   what to do next, do NOT summarise what you've done so far.

## Human attention

Before entering the loop, run `bd human list --json` once to inventory work
already waiting for the user. Never select a `human`-labelled bead for automatic
work.

When progress genuinely requires human judgement, access, hardware, credentials,
or observation:

1. Use `bd comments add <id> "<checklist>"` to record exactly what the user must do.
2. Add the label with `bd label add <id> human`.
3. Run `bd update <id> --status=open`; never leave the waiting bead `in_progress`.
4. Run `bd human list --json` and verify the bead appears.
5. Preserve coherent partial work, then continue with the next agent-ready bead.

Create a separate blocker bead and dependency only when the human action is a
distinct work item; otherwise flag the original bead. Keep any new blocker
inside the active scope. If new evidence removes the need for a person, comment
with that evidence, run `bd label remove <id> human`, and verify through
`bd human list --json` before resuming. Never call `bd human respond` or
`bd human dismiss` on the user's behalf.

## Rules

- **Never stop.** After closing an issue, immediately start the next one.
- **No lengthy analysis.** Glance at max 5 top-priority issues, pick one, go.
- **No asking for permission.** Just do the work.
- If `bd ready` returns no issues, run `bd human list` before stopping. Report
  that the agent-ready queue is empty and list any human-needed beads separately.
  When a scope was given, say which scope was exhausted; do not imply the human
  queue shares that scope unless it was filtered separately.
- If you hit an agent-resolvable blocker, create a new bead for it
  (`bd create ...`), add the dependency (`bd dep add ...`), and move on. Give
  the new bead the same label, or the same `--parent`, as the bead it came from,
  so it stays inside the scope. For human-only blockers, use the human-attention
  protocol above instead of leaving an ordinary blocker.
- Keep commits atomic, and push frequently where pushing is permitted.

## Pushing

Push after each issue by default — that is what keeps this loop useful to
anyone watching it.

But the repository's own rules win. Do NOT push when the project's agent
instructions, its Beads profile, or a current user or orchestrator instruction
prohibits or restricts it. A conservative or minimal Beads profile, or an
explicit "do not push", means commit only.

Do not treat this command as authority to override such a rule; it is not.
When pushing is blocked, keep grinding through issues and committing as
normal, and say once that pushes are being held back and why.
