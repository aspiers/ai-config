---
description: Grind through beads in priority order non-stop
allowed-tools: Bash(bd ready:*), Bash(bd show:*), Bash(bd update:*), Bash(bd close:*), Bash(bd create:*), Bash(bd dep:*)
---

Work through beads continuously in priority order. DO NOT STOP between issues.

## Workflow

Loop forever:

1. Run `bd ready` to get the list of ready (unblocked) issues.
2. Look at the top 5 highest-priority issues from the output. Do NOT
   spend time analysing beyond these 5. Pick whichever one you can
   make the most immediate progress on.
3. Mark it in progress: `bd update <id> --status=in_progress`
4. Show issue details: `bd show <id>`
5. Implement the work. Follow normal development practices (tests,
   linting, commits) but stay focused and move fast.
6. When done, close it: `bd close <id>`
7. Commit and push your changes.
8. **Go immediately to step 1.** Do NOT pause, do NOT ask the user
   what to do next, do NOT summarise what you've done so far.

## Rules

- **Never stop.** After closing an issue, immediately start the next one.
- **No lengthy analysis.** Glance at max 5 top-priority issues, pick one, go.
- **No asking for permission.** Just do the work.
- If `bd ready` returns no issues, report that the queue is empty and stop.
- If you hit a blocker you cannot resolve, create a new bead for it
  (`bd create ...`), add the dependency (`bd dep add ...`), move on
  to the next ready issue.
- Keep commits atomic and pushed frequently.
