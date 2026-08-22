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

Load and apply the `beads-best-practices` skill throughout. Its honest-WIP,
comment, and human-attention rules remain authoritative in this parallel
workflow.

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
fallback produces worktrees with no dependencies installed and no lifecycle
hooks run, and the damage is not obvious until later. Point the user at
<https://worktrunk.dev> (the CLI, and the plugin providing the skill) and
let them decide.

Consult the `worktrunk` skill, rather than guessing, whenever a run needs
more than the handful of commands below: reading or changing `.config/wt.toml`
or the user config, understanding why a hook fired or did not, resolving a
template-path question, or debugging any unexpected `wt` behaviour.

Two consequences worth internalising:

- **`wt` decides where worktrees live.** Paths come from a configurable
  template, so never invent one. Get the real path from the JSON output of
  `wt switch` (see below) or from `wt list`.
- **Hooks may already do the work you were about to do.** `wt hook show`
  lists what the repo has configured. If a `pre-merge` hook already runs
  the tests, do not run them a second time by hand; if there is none, you
  run them yourself after each merge.

- **How a merge is shaped is not this skill's business.** Squashing,
  rebasing, and whether a merge commit is created are matters of the user's
  general git and `wt` preferences, not of grinding beads in parallel.
  Never pass flags to force a particular shape.

## Decide the concurrency limit first

The arguments may already name a maximum ("3 at a time", "max 4 in
parallel", "-j2"). If so, use it, and do not ask.

If they do not, **ask before starting any work** — use `AskUserQuestion`
with 2 / 3 / 4 as the options, noting that the user can type another number.
Do not pick a default and proceed; the right number depends on how heavy the
project's test suite is and on what else the machine is doing.

The limit is a cap on *concurrently running subagents*, not a batch size.
Whenever a slot frees, refill it from the queue.

**Refilling is part of finishing a merge, not a separate step to report and
await approval on.** After merging and verifying, check the queue and
dispatch into every free slot in the same turn. A cap is a ceiling, not a
request for permission each time — "do not exceed N" is not "do not launch
without being asked", and a slot left idle while beads are unclaimed is
wasted wall-clock time.

Hold a slot empty only for a stated reason, and say the reason in a clause:
the user asked you to hold, or a running subagent is benchmarking and a
second CPU-heavy job would corrupt its measurements. Otherwise fill it.

Never state how many subagents are running from memory. Check first — see
**Establishing state** below.

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

## Keep the human-attention queue separate

Run `bd human list --json` during preflight and again before the final report.
Every automatic queue read must use `bd ready --exclude-label=human` in
addition to the active scope, so work waiting for a person is never dispatched
to another agent as if it were ready.

When a subagent or the orchestrator discovers that progress genuinely requires
human judgement, access, hardware, credentials, or observation:

1. Use `bd comments add <id> "<checklist>"` to record what the user must do.
2. Add `human` with `bd label add <id> human`.
3. Run `bd update <id> --status=open`, never leaving the waiting bead
   `in_progress`.
4. Run `bd human list --json` and verify that it appears.
5. Preserve coherent partial work, clean up its worktree safely, and refill the
   slot with agent-ready work.

Create and link a separate blocker bead only when the human action is a
distinct work item; otherwise flag the original bead. Keep a new blocker inside
the active scope. If new evidence removes the need for a person, comment with
that evidence, run `bd label remove <id> human`, and verify it disappears from
`bd human list --json` before resuming. Never use `bd human respond` or
`bd human dismiss` on the user's behalf.

## Preflight

Before dispatching anything:

0. Run `bd human list --json` and record the existing human-attention queue.
1. Confirm both prerequisites: run `wt --version`, and load the upstream
   `worktrunk` skill. Stop if either is unavailable.
2. Note the current branch. It is the **base branch**: every worktree
   branches from its tip, and every merge lands on it. Pass it explicitly
   to `wt` rather than relying on the default, which is the repository's
   default branch and may not be where you are.
3. `git status` — uncommitted work in the base worktree is not overwritten
   by `wt merge` (it advances the branch rather than merging into your
   working tree), but a dirty tree makes it hard to tell your own changes
   from the merged ones. If it is dirty, say so and ask whether to commit,
   stash, or proceed.
4. `wt hook show` — see which lifecycle hooks the repo configures, so you
   know what will run on create and merge, and what you still have to do
   yourself.
5. `wt list` — check for leftover `bgp/*` worktrees from an interrupted
   earlier run, and clean them up before starting.

Do not pick worktree paths yourself; `wt` derives them from its own config.

## Selecting a batch

Run `bd ready --exclude-label=human` with the scope flags, **freshly, every
time you are about to dispatch** — at the start, and again each time a slot
frees. Never reuse an
earlier listing or a remembered ordering. The human can reprioritise, close,
add, or block beads at any moment while the grind runs, and a run that is
overlapping work by design spends long stretches between queue reads. A
listing taken before the last merge may already be stale.

Consider only the top few highest-priority issues — enough to fill the free
slots, not the whole queue. Then filter for **parallel safety**, and this is
the one place worth spending a little thought:

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

   If the harness lets you title or label a subagent — Claude Code's `Agent`
   tool takes a short `description`, other harnesses have their own
   equivalent — **prefix it with the bead ID**, as in
   `<id>: rename config loader`. With several subagents running at once,
   the label is often the only thing distinguishing them in a progress
   display, and an untitled or generically-titled batch makes it impossible
   to tell which bead is which when one stalls or fails. It also matches the
   `bgp/<id>` branch and worktree names, so a label, a branch, and a bead
   line up on sight. If the harness offers no such field, skip this — it is
   presentation, not correctness.

The subagent's prompt must be self-contained, because it cannot see this
conversation. Include:

- The absolute path of its worktree, and an instruction to do **all** work
  there and nowhere else. It must not `cd` into the main repository.
- The bead's ID, title, description, design notes, and acceptance criteria —
  pasted in full, not referenced.
- **Bead bookkeeping rules — include these verbatim in every dispatch, and
  do not drop them when a brief gets long.**

  A subagent **must** keep its bead current as it works. `bd comment` is
  mandatory, not optional: findings, evidence, measurements, refuted
  hypotheses, dead ends, and anything the next person would otherwise have
  to rediscover — recorded **as they are found**, not saved for the end.

  This is the only durable record. A final report is lost entirely if the
  subagent is stopped, crashes, or loses its connection mid-run, and that is
  not hypothetical: in one run three subagents were interrupted, and their
  discoveries survived only because someone happened to notice and
  transcribe them by hand. A comment written at the moment of discovery
  survives anything.

  A subagent **must never** change a bead's status — above all, **never
  `bd close`**. Closing marks the work done *before it is merged*, from a
  worktree whose branch may still be rejected at the gate, and a closed bead
  with unmerged work is worse than an open one because nothing will bring you
  back to it. Closure means *integrated into the trunk and verified there*,
  which only the orchestrator can know. Status transitions and closure are
  the orchestrator's alone.

  Nor should a subagent create beads for work it discovers. Have it report
  those in its output or as a comment on its own bead; the orchestrator
  files them, so scope labels and parents stay consistent and duplicates are
  caught against the queue the subagent cannot see.

  If only a person can unblock the bead, the subagent must immediately add a
  checklist comment describing the required human action and call it out in
  its report. It must not change labels or status; the orchestrator applies
  the human-attention protocol after preserving the branch.

  Some setups back the database with a single server process (a lockfile,
  PID or port under `.beads/`). That is a reason to expect occasional
  contention on a write, not a reason to stop subagents commenting — have
  them retry. Never respond to it by banning `bd` outright: doing so trades
  a recoverable retry for the permanent loss of everything an interrupted
  subagent had learned.
- The project's development expectations: tests, linting, and the
  repository's commit conventions.
- An instruction to commit its work to its branch and **not to push at
  all**, and not to merge, rebase, or otherwise touch other branches.

  Say this as a flat prohibition. Phrasing like "push only your own branch"
  is meant as *don't push to the base* but reads as an instruction to push,
  and subagents will follow it. There is no reason for them to: `wt merge`
  integrates from the **local** branch, so committing is sufficient, and
  every pushed branch outlives its worktree as remote litter that no
  teardown removes.
- An instruction not to run `wt` at all, and not to merge. Worktree
  lifecycle and integration belong to the orchestrator; a subagent merging
  would write to the shared base branch concurrently with its siblings.
- A request to report back: what changed, which files, what it ran to verify,
  and anything it could not finish or discovered along the way.

Gitignored files do not exist in a fresh worktree unless a `pre-start` hook
creates them or you copied them with `wt step copy-ignored`. If a bead needs
something neither provides, run it serially instead.

## Merging back

Merge **one branch at a time**, in whatever order the subagents finish.

Use `wt merge`, driven at the subagent's worktree from where you are. It
rebases the branch onto the base before merging, and **that is why it is
the right tool for a parallel grind**: a conflict stops with the rebase
left open *in the bead's own worktree*, leaving the base branch untouched.
The mess stays isolated where it belongs, instead of sitting half-merged in
the shared base worktree and blocking every sibling behind it.

Note that `wt merge` works in the opposite direction to `git merge`: it
merges *the worktree's branch into the target*. For each finished bead:

1. Read the subagent's report. If it failed or stopped short, do not merge;
   go to **When a subagent fails** below.
2. Merge it:

   ```bash
   wt -C <worktree-path> merge <base-branch> -y
   ```

   This runs the repo's `pre-merge` hooks (its own quality gate), rebases
   the branch onto the base, merges it, then removes the worktree and
   branch. One command covers merge and teardown. Pass no shape flags —
   squash, rebase and merge-commit behaviour come from the user's `wt`
   config, not from this skill.
3. If a `pre-merge` hook fails, the merge aborts and nothing lands. Fix the
   problem in the worktree, or treat the bead as failed. Never pass
   `--no-hooks` to force it through — the hook is the repo's gate, and this
   skill is not authority to bypass it.
4. If the rebase conflicts, the branch is left mid-rebase in its worktree
   and the base is untouched. Resolve it there, `git rebase --continue`,
   then re-run the merge. You have the full picture; the subagent does not,
   and re-dispatching to it will not help. If it is not worth resolving,
   `git rebase --abort` and treat the bead as failed.
5. Run the project's tests and linters after each merge **unless a
   `pre-merge` hook already ran them** — no point duplicating the gate. The
   reason to verify per-merge is to know which merge broke what: a branch
   that passed alone can still break once combined with a sibling's work.

   **A skipped gate is not a passing gate.** Some gates disable themselves
   when a prerequisite is missing — an absent build tree, an uninstalled
   tool — and report a cheerful skip rather than a failure. Read what the
   gate actually did, not just its exit status, and treat "did not run" as
   the same severity as "failed". The same applies to a subagent reporting
   "all gates pass": check whether any of them skipped.

   Where a subagent's central claim is checkable, check it rather than
   accepting the report — inject the defect its fix prevents and confirm the
   gate rejects it, then restore. A fix that cannot be shown to fail without
   it has not been verified.
6. `bd close <id>` once merged and green. Close it now, in this step —
   closing is part of finishing the merge, and the moment attention moves to
   the next subagent is exactly when a bead gets left in `in_progress`.
7. Refill the free slot from the queue and dispatch again, in this same turn.

Do not batch the merges. Do not close a bead before its branch is merged and
verified — a closed bead with unmerged work is worse than an open one.

## Establishing state — never infer it

Every question about what is running, where, and how far along has a command
that answers it. Use the command. Inferring from memory or from a remembered
path is how a long run drifts away from reality, and the errors compound
silently because a wrong answer looks exactly like a right one.

| Question | Authority |
| --- | --- |
| Where are the worktrees? | `git worktree list` (or `wt list`) |
| What is uncommitted, and how far ahead/behind? | `wt list` |
| How many subagents are running? | The harness — its own task list or progress display |
| What is claimed and by whom? | `bd list --status=in_progress` |
| Did a branch's work land on the base? | `git log <base> -- <path>`, then diff the content |

That last row has a trap worth knowing. `wt merge` **rebases** the branch
onto the base before merging, so every commit gets a **new SHA**. Asking
whether the original commit is an ancestor —
`git merge-base --is-ancestor <sha> <base>` — correctly answers *no* for work
that landed perfectly. Ask whether the **content** arrived instead: check the
file exists on the base and diff it against the branch. A subagent that
checks its own SHAs will conclude its work was lost when it was not.

Specifically:

- **Never glob a remembered worktree path.** `wt` derives paths from its own
  config, and a repository can hold worktrees under several parents. A
  relative glob is worse still: it resolves against your current directory,
  which may itself have drifted into a worktree, and then silently returns
  nothing.
- **Never count `bgp/*` branches to count subagents.** Branches outlive the
  agents that made them — a paused bead, a merged-but-unpruned branch, and a
  live agent all look identical in `git branch`.
- **A query that returns nothing about state you believe exists is evidence
  the query is wrong**, not that the state is gone. Verify the query before
  acting on an empty result.

## When a subagent is paused or interrupted

Distinct from failure, and more dangerous, because the work usually still
exists and is easy to destroy by accident.

**There is no pause primitive.** Stopping a subagent terminates it. If asked
to pause, say so and ask whether to stop them or let them finish; do not
silently substitute one for the other.

**Before stopping anything, have it commit.** A subagent's uncommitted work
lives only in its worktree's working tree — not in the reflog, not in the
index, not in dangling objects, not in any stash. If the worktree is later
removed, the work is genuinely gone. So instruct subagents to commit
work-in-progress to their own branch early and often, and prefer letting one
finish over stopping it mid-edit.

**If a subagent has already stopped without committing**, commit on its
behalf, in its worktree, labelled clearly as unverified:

```bash
git -C <worktree-path> add -A
git -C <worktree-path> commit -m "wip(<scope>): preserve interrupted work"
```

Do this **only once the subagent is confirmed finished**. Committing under a
live subagent moves its branch pointer mid-edit and races it.

**A transient error is not death.** A notification reporting a stalled
stream, a network drop, or an API error describes a broken connection; the
subagent may still be running and may resume. Neither silence nor an error
justifies dismantling a worktree. Ask it directly if the harness supports
messaging, or wait for a real completion notification.

**Never re-dispatch a bead into an existing worktree.** If a subagent was
stopped or interrupted, its worktree and branch usually survive. Sending a
second subagent to the same `bgp/<id>` puts two of them in one working tree,
committing over each other — one will sweep the other's uncommitted changes
into a commit whose message describes something else entirely, and history
stops matching content.

Before re-dispatching, run `git worktree list` and decide explicitly:

- **Resume the same subagent** (if the harness can message it) — best, since
  it keeps its accumulated context.
- **Reuse the worktree with a new subagent** — only after confirming the old
  one is finished. Tell the new one exactly what state it will find and that
  any existing commits are a predecessor's, not its own.
- **Start clean** — remove the worktree first, having preserved anything
  uncommitted.

What you must not do is dispatch and hope. If a subagent reports finding
changes it did not make, treat that as a coordination failure on your side,
not a curiosity: stop dispatching into that worktree until you know who else
is in it.

**Before concluding any work is lost, look in the worktree.** Searching the
reflog, index, dangling objects and stashes is a sound search aimed at the
wrong place: uncommitted changes live in none of those stores.

## When a subagent fails

Do not retry blindly, and do not leave the bead in limbo:

- **Reported a human-only blocker**: preserve coherent partial work, then use
  the human-attention protocol above. Flag the original bead unless the human
  action is a distinct work item; in that case create the blocker, keep it in
  scope, add the dependency, and flag that blocker. Return the original bead
  to `open` and verify the flagged bead through `bd human list --json`.
- **Reported an agent-resolvable blocker**: create a bead for the blocker
  (`bd create ...`), add the dependency (`bd dep add ...`), and return the
  original bead to `open` with `bd update <id> --status=open`. Give the new
  bead the same label or `--parent` so it stays inside the scope.
- **Produced partial work worth keeping**: merge it if it is coherent and
  green on its own, then reopen the bead with a note about what remains.
  Otherwise discard the branch.
- **Produced nothing usable**: discard the branch, reopen the bead, and
  either take it serially yourself or move on.

Always remove the worktree afterwards, whatever the outcome. Stale worktrees
accumulate and confuse the next run. A successful `wt merge` already removed
it; otherwise discarding abandoned work needs both force flags:

```bash
wt remove bgp/<id> --force --force-delete -y
```

`--force` covers a dirty worktree, `--force-delete` an unmerged branch.
Both are needed to discard abandoned work, so be sure that is the intent —
this throws the subagent's commits away. To keep the branch for inspection,
drop `--force-delete` and use `--no-delete-branch`.

## When priorities shift under a running batch

A parallel grind can have several beads in flight for a long time, so the
backlog it was dispatched from may no longer be the backlog the human cares
about. Each time you re-read `bd ready`, compare the top of the fresh queue
against what is currently in flight.

**Never discard or roll back in-flight work.** A subagent's commits are
finished effort; losing them to a reshuffled backlog is strictly worse than
landing something the human deprioritised. Merge what completes, as normal.

If, and only if, there is a **large** discrepancy — the top of the fresh
queue is markedly higher priority than everything currently in flight, e.g.
a new P0/P1 sitting behind a batch of P3s — draw the human's attention to it
and **carry straight on working**:

- Say it once, briefly, in your normal output: which in-flight beads, which
  higher-priority ones now waiting, and that they can tell you to pause the
  batch if they would rather you switched.
- Fire an out-of-band notification, so it lands even when nobody is reading
  the transcript:

  ```bash
  ai-notify "Beads priority discrepancy" \
            "<in-flight beads> running while <higher-priority beads> wait"
  ```

  `ai-notify` picks whichever mechanism the machine actually has, makes the
  notification persistent where it can (the human may be away from the
  screen), and always exits 0 — so there is nothing to check and no need to
  probe for `herdr`, `notify-send`, or anything else yourself. It never waits
  for input. If it is not installed, skip the notification; the in-transcript
  mention is enough.

**This must never block.** Do not use `AskUserQuestion`, do not wait for a
reply, do not slow the loop down. Mention it, notify, and continue exactly as
before. Pause only if the human explicitly asks you to — an unanswered
question here would stall the grind for hours, which is far worse than
finishing some lower-priority work first.

Say it once per discrepancy, not once per loop iteration. Repeating the same
alert every cycle is noise, and noise gets ignored.

## Continuing and stopping

Keep refilling slots until `bd ready --exclude-label=human` returns nothing
within scope. Then wait for the in-flight subagents, merge their branches, and
stop.

Run `bd human list` before the final report. State that the **agent-ready**
queue is empty, then list human-needed beads separately with their requested
actions. When a scope was given, name it, so it is clear the agent-ready queue
is empty *within that scope* rather than overall; do not imply the human queue
shares that scope unless it was filtered separately.

Between merges, do not pause to ask what to do next and do not summarise
progress — keep the loop running. The exception is the concurrency question
at the very start, and anything that genuinely needs a decision you cannot
make (a dirty working tree, an ambiguous scope, a merge conflict whose
correct resolution is a judgement call about intent). A shifted backlog is
**not** such a case — flag it and keep going, as above.

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

**Check the remote too.** `wt merge` removes the local branch and worktree,
but anything a subagent pushed survives on the remote and no teardown step
removes it. A long run leaves one stale `bgp/*` branch per bead:

```bash
git ls-remote --heads <remote> 'refs/heads/bgp/*'
```

**Verify with `git cherry`, not ancestry.** Because `wt merge` rebases,
merged branches have different SHAs, so `git log <base>..<branch>` and
`git merge-base --is-ancestor` both report unmerged work that landed
perfectly. `git cherry` compares by patch *content* and sees through the
rebase:

```bash
git cherry <base> <remote>/bgp/<id>   # lines starting '+' are genuinely unmerged
```

Delete only branches with no `+` lines, and report any that do rather than
forcing them.
