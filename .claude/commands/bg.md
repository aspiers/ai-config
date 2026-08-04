---
description: Grind through beads in priority order non-stop
argument-hint: <optional scope - label / epic ID / priority / type>
allowed-tools: Bash(bd ready:*), Bash(bd show:*), Bash(bd update:*), Bash(bd close:*), Bash(bd create:*), Bash(bd dep:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*)
---

Work through beads continuously in priority order. DO NOT STOP between issues.

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

1. Run `bd ready` with the scope flags to get the list of ready (unblocked)
   issues.
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

## Rules

- **Never stop.** After closing an issue, immediately start the next one.
- **No lengthy analysis.** Glance at max 5 top-priority issues, pick one, go.
- **No asking for permission.** Just do the work.
- If `bd ready` returns no issues, report that the queue is empty and stop.
  When a scope was given, say which scope was exhausted, so it is clear that
  the queue is empty within that scope rather than overall.
- If you hit a blocker you cannot resolve, create a new bead for it
  (`bd create ...`), add the dependency (`bd dep add ...`), move on
  to the next ready issue. Give the new bead the same label, or the same
  `--parent`, as the bead it came from, so it stays inside the scope.
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
