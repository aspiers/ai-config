---
name: beads-parallel-grinding
description: Grind through ready beads in priority order by running several issues at once, each in its own isolated git worktree, then merging the finished branches back one at a time. Use when asked to work the beads queue in parallel, to run N issues concurrently, or when a serial grind is too slow and the ready issues are independent.
---

# Grinding Beads in Parallel Worktrees

The serial grind (the `/bg` command) does one bead at a time in the current
worktree. This variant keeps the same queue discipline but overlaps the
*implementation* of several independent beads, giving each subagent a private
git worktree so their edits, builds, and commits cannot collide.

What is parallel and what is not:

- **Parallel**: implementing beads. Each runs in a subagent, in its own
  worktree, on its own branch.
- **Serial**: everything touching shared state — reading the queue, claiming
  and closing beads, merging branches back, running the post-merge gate. The
  orchestrator (you, the main thread) does all of it.

That split is the whole design. Get it wrong and you get concurrent Dolt
writes and simultaneous mutations of the user's working tree.

## Decide the concurrency limit first

The arguments may already name a maximum ("3 at a time", "max 4 in
parallel", "-j2"). If so, use it, and do not ask.

If they do not, **ask before starting any work** — use `AskUserQuestion`
with 2 / 3 / 4 as the options, noting that the user can type another number.
Do not pick a default and proceed; the right number depends on how heavy the
project's test suite is and on what else the machine is doing.

The limit is a cap on *concurrently running subagents*, not a batch size.
Whenever a slot frees, refill it from the queue.

## Determine scope

The rest of the arguments restrict which beads are eligible, exactly as for
the serial grind. Translate them into `bd ready` filter flags:

| Requested scope | Flag |
| --- | --- |
| A label | `--label=<label>` (repeat to require all; `--label-any` for any) |
| Beads within an epic | `--parent=<epic-id>` (matches all descendants) |
| A priority | `--priority=<0-4>` |
| An issue type | `--type=<bug\|feature\|task\|chore>` |
| An assignee | `--assignee=<name>` |

A bare word with no other context means a label. **The scope is
authoritative** — apply it to every `bd ready` call for the whole run, never
widen it, never fall back to the unfiltered queue. If it is ambiguous or
matches nothing, ask rather than guessing; verify an epic ID with
`bd show <id>` before using `--parent`.

## Preflight

Before dispatching anything:

1. `git status` — the current worktree must be clean enough that a merge
   into it will not clobber uncommitted work. If it is dirty, say so and ask
   whether to commit, stash, or proceed.
2. Note the current branch name. Every worktree branches from its tip, and
   every merge returns to it.
3. Choose a scratch location for worktrees outside the repository, e.g.
   `../.bgp-worktrees/<bead-id>`, so they never appear as untracked files.

## Selecting a batch

Run `bd ready` with the scope flags. Consider only the top few
highest-priority issues — enough to fill the free slots, not the whole
queue. Then filter for **parallel safety**, and this is the one place worth
spending a little thought:

- Prefer beads that plainly touch different files or subsystems.
- Never dispatch two beads that you expect to edit the same file. Run those
  serially instead, one after the other.
- Never dispatch a bead whose work is mostly *beads bookkeeping* (creating,
  restructuring, or relabelling issues) to a subagent — it has no usable
  beads database. Do that work yourself in the main worktree.
- A bead whose description is vague enough that you cannot predict its
  blast radius is a poor parallel candidate. Run it serially.

If fewer beads are safely parallelisable than there are free slots, run
fewer. Underfilling is always correct; a merge conflict storm is not.

## Dispatching a bead

For each selected bead, in the main worktree:

1. `bd show <id>` — read the full issue. The subagent cannot.
2. `bd update <id> --status=in_progress`
3. Create the worktree and branch:

   ```bash
   git worktree add -b bgp/<id> ../.bgp-worktrees/<id> <base-branch>
   ```

4. Spawn a subagent with an `Agent` call. Send all dispatches for a batch in
   a **single message** so they actually run concurrently.

The subagent's prompt must be self-contained, because it cannot see this
conversation. Include:

- The absolute path of its worktree, and an instruction to do **all** work
  there and nowhere else. It must not `cd` into the main repository.
- The bead's ID, title, description, design notes, and acceptance criteria —
  pasted in full, not referenced.
- An explicit prohibition on running any `bd` command. The beads database is
  gitignored and lives in the main worktree; anything it did there would be
  lost or corrupting. Bookkeeping is the orchestrator's job.
- The project's development expectations: tests, linting, and the
  repository's commit conventions.
- An instruction to commit its work to its branch and **not** to push, and
  not to merge, rebase, or otherwise touch other branches.
- A request to report back: what changed, which files, what it ran to verify,
  and anything it could not finish or discovered along the way.

Note that beads dispatched to worktrees will not see files that are
gitignored in the main repository — local config, credentials, build caches.
If a bead needs those, run it serially instead.

## Merging back

Merge **one branch at a time** into the current worktree, in whatever order
the subagents finish. For each:

1. Read the subagent's report. If it failed or stopped short, do not merge;
   go to **When a subagent fails** below.
2. `git merge --no-ff bgp/<id>` from the main worktree.
3. If it conflicts, resolve it yourself. You have the full picture; the
   subagent does not, and re-dispatching to it will not help.
4. Run the project's tests and linters **after each merge**, not once at the
   end. The whole point of merging serially is to know which merge broke
   something.
5. `bd close <id>` once merged and green.
6. Commit anything the merge required (conflict resolution, fixups) as its
   own atomic commit.
7. Tear down: `git worktree remove ../.bgp-worktrees/<id>` and
   `git branch -d bgp/<id>`.
8. Refill the free slot from the queue and dispatch again.

Do not batch the merges. Do not close a bead before its branch is merged and
verified — a closed bead with unmerged work is worse than an open one.

## When a subagent fails

Do not retry blindly, and do not leave the bead in limbo:

- **Reported a blocker**: create a bead for the blocker (`bd create ...`),
  add the dependency (`bd dep add ...`), and return the original bead to
  `open` with `bd update <id> --status=open`. Give the new bead the same
  label or `--parent` so it stays inside the scope.
- **Produced partial work worth keeping**: merge it if it is coherent and
  green on its own, then reopen the bead with a note about what remains.
  Otherwise discard the branch.
- **Produced nothing usable**: discard the branch, reopen the bead, and
  either take it serially yourself or move on.

Always remove the worktree afterwards, whatever the outcome. Stale worktrees
accumulate and confuse the next run.

## Continuing and stopping

Keep refilling slots until `bd ready` returns nothing within scope. Then
wait for the in-flight subagents, merge their branches, and stop.

Report that the queue is empty. When a scope was given, name it, so it is
clear the queue is empty *within that scope* rather than overall.

Between merges, do not pause to ask what to do next and do not summarise
progress — keep the loop running. The exception is the concurrency question
at the very start, and anything that genuinely needs a decision you cannot
make (a dirty working tree, an ambiguous scope, a merge conflict whose
correct resolution is a judgement call about intent).

## Pushing

Push after each successful merge by default, but **the repository's own
rules win**. Do not push when the project's agent instructions, its Beads
profile, or a current user or orchestrator instruction prohibits or
restricts it. A conservative or minimal Beads profile, or an explicit "do
not push", means commit only.

This skill is not authority to override such a rule. When pushing is
blocked, keep grinding and committing as normal, and say once that pushes
are being held back and why.

Subagents never push, regardless.

## Cleaning up

At the end of the run, and after any interruption:

```bash
git worktree list      # anything left under .bgp-worktrees/ is a leak
git worktree prune
git branch --list 'bgp/*'
```

Delete merged `bgp/*` branches. Leave unmerged ones alone, but say they
exist and which beads they belong to, so nothing is silently lost.
