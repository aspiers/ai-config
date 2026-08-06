---
name: beads-parallel-grinding
description: Grind through ready beads in priority order by running several issues at once, each in its own isolated git worktree managed by worktrunk (`wt`), then merging the finished branches back one at a time. Use when asked to work the beads queue in parallel, to run N issues concurrently, or when a serial grind is too slow and the ready issues are independent.
compatibility: Requires the `wt` CLI (worktrunk, https://worktrunk.dev), the upstream `worktrunk` skill, and the `bd` CLI (beads)
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
  and closing beads, merging branches back, and verifying each merge. The
  orchestrator (you, the main thread) does all of it.

That split is the whole design. Get it wrong and you get concurrent Dolt
writes and simultaneous mutations of the user's working tree.

## Use `wt` for all worktree operations

Worktree creation, merging, and removal go through **worktrunk** (`wt`),
never through raw `git worktree` or `git merge`. A repository can configure
lifecycle hooks — installing dependencies, copying env files, running the
test suite before a merge — and `wt` is what runs them. Reaching for plain
git skips the repo's own setup and gates, which is exactly the failure this
skill exists to avoid.

### Both prerequisites are required

This skill deliberately does not restate how `wt` works. It covers only the
orchestration — which beads to run in parallel, who merges, and in what
order — and delegates everything about `wt` itself to upstream. So it needs
two things present, and **checks both before doing any work**:

1. **The `wt` CLI.** Verify with `wt --version`.
2. **The upstream `worktrunk` skill.** Load it before the first `wt`
   command. It is the authority on `wt` configuration, hook types and
   timing, template variables, and troubleshooting — all of which this
   skill assumes rather than explains.

If either is missing, **stop and say which**. Do not fall back to
`git worktree`, and do not improvise `wt` usage from memory. A silent
fallback produces worktrees with no dependencies installed and merges with
no pre-merge gate, and the damage is not obvious until later. Point the
user at <https://worktrunk.dev> (the CLI, and the plugin providing the
skill) and let them decide.

Consult the `worktrunk` skill, rather than guessing, whenever a run needs
more than the handful of commands below: reading or changing `.config/wt.toml`
or the user config, understanding why a hook fired or did not, resolving a
template-path question, or debugging any unexpected `wt` behaviour.

Two consequences worth internalising:

- **`wt` decides where worktrees live.** Paths come from a configurable
  template, so never invent one. Get the real path from the JSON output of
  `wt switch` (see below) or from `wt list`.
- **Hooks may already do the work you were about to do.** `wt hook show`
  lists what the repo has configured. If a `pre-merge` hook already runs the
  tests, do not run them a second time by hand; if there is none, you run
  them yourself after each merge.

**Never squash.** A bead can legitimately produce several atomic commits,
and collapsing them destroys commit boundaries chosen deliberately while
the work was done. `wt merge` squashes by default, so every merge here
passes `--no-squash` explicitly — even where the user config already sets
`[merge] squash = false`, since that config is per-machine and this skill
must stay correct without it. Squashing is never enabled to tidy history.

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

0. Confirm both prerequisites: run `wt --version`, and load the upstream
   `worktrunk` skill. Stop if either is unavailable.
1. Note the current branch. It is the **base branch**: every worktree
   branches from its tip, and every merge lands on it. Pass it explicitly
   to `wt` rather than relying on the default, which is the repository's
   default branch and may not be where you are.
2. `git status` — uncommitted work in the main worktree is not overwritten
   by `wt merge` (it advances the branch, it does not merge into your
   working tree), but a dirty tree makes it hard to tell your own changes
   from the merged ones. If it is dirty, say so and ask whether to commit,
   stash, or proceed.
3. `wt hook show` — see which lifecycle hooks the repo configures, so you
   know what will run on create and merge, and what you still have to do
   yourself.
4. `wt list` — check for leftover `bgp/*` worktrees from an interrupted
   earlier run, and clean them up before starting.

Do not pick worktree paths yourself; `wt` derives them from its own config.

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
3. Create the worktree and branch with `wt`, from the main worktree:

   ```bash
   wt switch --create bgp/<id> --base <base-branch> \
             --no-cd --format=json -y
   ```

   `--no-cd` keeps your own shell where it is — you are orchestrating, not
   moving in. `--format=json` prints the result as structured output;
   **read the worktree path from it** rather than guessing, since the path
   comes from `wt`'s configured template. `-y` skips approval prompts, which
   nothing is present to answer.

   This is the step that runs the repo's `pre-start` hooks, so the subagent
   starts in a worktree with dependencies installed and env files in place.
   Let it finish before dispatching.

   If the bead needs gitignored files that hooks do not provide (local
   config, caches), copy them over with
   `wt step copy-ignored <worktree-path>` before dispatching.

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
- An instruction not to run `wt` at all. Worktree lifecycle — creating,
  merging, removing — belongs to the orchestrator. A subagent running
  `wt merge` would merge into the shared base branch concurrently with its
  siblings.
- A request to report back: what changed, which files, what it ran to verify,
  and anything it could not finish or discovered along the way.

Gitignored files do not exist in a fresh worktree unless a `pre-start` hook
creates them or you copied them with `wt step copy-ignored`. If a bead needs
something neither provides, run it serially instead.

## Merging back

Merge **one branch at a time**, in whatever order the subagents finish.
Note that `wt merge` works in the opposite direction to `git merge`: it
merges *the worktree's branch into the target*, which is what is wanted
here. For each finished bead:

1. Read the subagent's report. If it failed or stopped short, do not merge;
   go to **When a subagent fails** below.
2. Merge it, driving `wt` at the subagent's worktree from where you are:

   ```bash
   wt -C <worktree-path> merge <base-branch> --no-squash --no-ff -y
   ```

   `--no-squash` is **mandatory** — never squash a bead's commits together.
   `--no-ff` joins the branch to the base with a merge commit instead of
   flattening it in, so each bead stays a visible unit of work in history.

   The rest of the pipeline stays on: this runs the repo's `pre-merge`
   hooks (its own quality gate), rebases the branch onto the base, adds the
   merge commit, then removes the worktree and branch. One command covers
   merge and teardown.
3. If a `pre-merge` hook fails, the merge aborts and nothing lands. Fix the
   problem yourself in the worktree, or treat the bead as failed. Never
   pass `--no-hooks` to force it through — the hook is the repo's gate, and
   this skill is not authority to bypass it.
4. If the rebase conflicts, it aborts immediately. Resolve it yourself in
   the worktree, then re-run the merge. You have the full picture; the
   subagent does not, and re-dispatching to it will not help.
5. Run the project's tests and linters after each merge **unless a
   `pre-merge` hook already ran them** — no point duplicating the gate. The
   reason to verify per-merge rather than once at the end is to know which
   merge broke what.
6. `bd close <id>` once merged and green.
7. Refill the free slot from the queue and dispatch again.

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
accumulate and confuse the next run. A successful `wt merge` already removed
it; otherwise do it explicitly:

```bash
wt remove bgp/<id> --force --force-delete -y
```

`--force` covers a dirty worktree, `--force-delete` an unmerged branch.
Both are needed to discard abandoned work, so be sure that is the intent —
this throws the subagent's commits away. To keep the branch for inspection,
drop `--force-delete` and use `--no-delete-branch`.

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
wt list                # any surviving bgp/* worktree is a leak
```

Remove leftovers with `wt remove bgp/<id> -y`. Without `--force-delete` it
declines to delete a branch holding unmerged work, which is the behaviour
you want here: leave those alone, and say they exist and which beads they
belong to, so nothing is silently lost.
