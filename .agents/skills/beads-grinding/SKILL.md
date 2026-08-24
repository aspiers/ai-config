---
name: beads-grinding
description: >-
  Grind through ready beads serially in priority order, one at a time in the
  current worktree, without stopping between issues. Use when asked to work
  the beads queue, grind the backlog, keep working through ready issues, or
  make unattended progress overnight. For concurrent worktrees instead, use
  beads-parallel-grinding.
---

# Grinding Beads Serially

Work through ready beads continuously in priority order, one at a time in the
current worktree. **Do not stop between issues.**

Load and apply the [`beads-best-practices`](../beads-best-practices/SKILL.md)
skill throughout, especially its human-attention and honest work-in-progress
rules.

For overlapping several beads at once in isolated worktrees, use
[`beads-parallel-grinding`](../beads-parallel-grinding/SKILL.md) instead. This
skill is the serial variant.

## Determine scope

The invocation may carry arguments restricting which beads are eligible. If
there are none, work through every ready bead.

Otherwise translate the restriction into filter flags for `bd ready`:

| Requested scope | Flag |
| --- | --- |
| A label | `--label=<label>` (repeat to require all; `--label-any` for any) |
| Beads within an epic | `--parent=<epic-id>` (matches all descendants) |
| A priority | `--priority=<0-4>` |
| An issue type | `--type=<bug\|feature\|task\|chore>` |
| An assignee | `--assignee=<name>` |

A bare word with no other context means a label, so a scope of `fiscal-host`
becomes `bd ready --label=fiscal-host`. Combine flags when the scope names
more than one restriction.

**The scope is authoritative.** Apply it to every `bd ready` call for the
whole run. Never widen it, and never fall back to the unfiltered queue.

If the scope is ambiguous, or names a label or epic that matches nothing, ask
the user rather than guessing — unless running unattended, where the
[unattended rules](#running-unattended) apply instead. Verify an epic ID
exists with `bd show <id>` before using `--parent`.

## Workflow

Loop forever:

1. Run `bd ready --exclude-label=human` with the scope flags to get the list
   of agent-ready (unblocked) issues. **Run it fresh every time round the
   loop.** Never reuse a listing from an earlier iteration or work from a
   remembered ordering — the human can reprioritise, close, add, or block
   beads at any moment, so a queue read one issue ago may already be wrong.
   Your own closes, new beads, and newly unblocked dependencies change it too,
   so this holds even when nobody is awake to reprioritise.
2. Look at the top 5 highest-priority issues from the output. Do NOT spend
   time analysing beyond these 5. Pick whichever one you can make the most
   immediate progress on.
3. Mark it in progress: `bd update <id> --status=in_progress`
4. Show issue details: `bd show <id>`
5. Implement the work. Follow normal development practices (tests, linting,
   commits) but stay focused and move fast.
6. When done, close it: `bd close <id>`
7. Commit your changes, and push them unless the repository's own rules say
   otherwise (see [Pushing](#pushing) below).
8. **Go immediately to step 1.** Do NOT pause, do NOT ask the user what to do
   next, do NOT summarise what you've done so far.

## Work that needs a person

Before entering the loop, run `bd human list --json` once to see what is
already waiting for the user.

**Every queue read must exclude the label:**

```bash
bd ready --exclude-label=human
```

A bead waiting on a person is usually blocked by nothing, so it appears in a
plain `bd ready` like any other issue — `bd ready` has no knowledge of the
label. Miss the flag once and you will pick up someone's decision as ordinary
work and decide it yourself. Treat it as an invariant on every call.

When progress needs a person's judgement, access, hardware, credentials, or
observation, **split the work at that point**. Their part becomes its own
bead; yours stays in the bead you are holding:

```bash
ask=$(bd create --title="Decide: <the question>" \
                --description="<context, options, what turns on each>" \
                --type=task --json | jq -r .id)
bd label add "$ask" human
bd dep add "$current" "$ask"
bd update "$current" --status=open
bd human list --json
```

Never label the bead you are working on and leave it at that. `bd human
respond` closes whatever it answers, so a bead holding both their decision and
your implementation gets closed with the implementation undone. One bead, one
doer — see
[`beads-best-practices`](../beads-best-practices/SKILL.md#one-bead-one-doer).

Keep the new bead inside the active scope, with the same label or `--parent`
as the bead it came from. Preserve coherent partial work, then move on to the
next ready bead.

The user answers these with `/blockers`
([`beads-blocker-review`](../beads-blocker-review/SKILL.md)), which closes each
bead and automatically releases whatever depended on it — so the work returns
to `bd ready` on its own. Do not answer them yourself, and do not keep checking
whether the blocker went away. Because step 1 re-reads the queue every
iteration, released work reappears without you doing anything.

Never call `bd human respond` or `bd human dismiss` on the user's behalf.

## Rules

- **Never stop.** After closing an issue, immediately start the next one.
- **No lengthy analysis.** Glance at max 5 top-priority issues, pick one, go.
- **Priorities are not static.** The human may reprioritise the backlog while
  you work. Treat every `bd ready` result as a snapshot valid only for the
  issue you are about to pick, and re-read the queue before each pick. Finish
  the issue in hand first, though — do not abandon work in progress because
  something else rose above it.
- **No asking for permission.** Just do the work.
- If `bd ready` returns no issues, run `bd human list` before stopping. Report
  that the agent-ready queue is empty and list any human-needed beads
  separately, pointing the user at `/blockers` to work through them. When a
  scope was given, say which scope was exhausted; do not imply the human queue
  shares that scope unless it was filtered separately.
- If you hit an agent-resolvable blocker, create a new bead for it
  (`bd create ...`), add the dependency (`bd dep add ...`), and move on. Give
  the new bead the same label, or the same `--parent`, as the bead it came
  from, so it stays inside the scope. When the blocker needs a person, split
  it into their own bead as above instead of leaving an ordinary blocker.
- Keep commits atomic, and push frequently where pushing is permitted.

## Pushing

Push after each issue by default — that is what keeps this loop useful to
anyone watching it.

But the repository's own rules win. Do NOT push when the project's agent
instructions, its Beads profile, or a current user or orchestrator instruction
prohibits or restricts it. A conservative or minimal Beads profile, or an
explicit "do not push", means commit only.

Do not treat an invocation of this skill as authority to override such a rule;
it is not. When pushing is blocked, keep grinding through issues and
committing as normal, and say once that pushes are being held back and why.

## Running unattended

An unattended run — the user is asleep or away, and has said so — changes what
to do when you would otherwise ask. Everything above still applies; these
rules sit on top.

**Never ask a question.** There is nobody to answer it, so a question stalls
the run until they return and wastes the whole opportunity. Where the workflow
above says to ask, use your best judgement and proceed instead. Getting it
wrong is recoverable — git history means anything can be reverted or rewound —
whereas stopping teaches nothing and cannot be recovered. Commit as you go so
that judgement calls are individually revertable.

**Best judgement covers approach, not the user's decisions.** How to
implement something is yours to decide anyway. A criterion genuinely needing
their observation, access, hardware, credentials, or choice is not — deciding
that yourself is
[closing around the human](../beads-best-practices/SKILL.md#do-not-close-around-the-human).
Split it into their own bead as above and carry on with other ready work.

Expect their queue to grow over a long unattended run. That is the run working
as intended, not a failure: the beads accumulate for a single review pass when
they return.

**Report on waking.** Run `bd human list` again at the end, and put it first —
those beads are what the user must act on before the work depending on them can
move, and `/blockers` is how they clear them. Then give a
concise account of what was achieved, with whatever supporting information is
needed to quickly test it. Distinguish an empty agent-ready queue from work
still waiting for the user.

## Related Skills

- [`beads-best-practices`](../beads-best-practices/SKILL.md) — issue-writing
  and update practices; authoritative for the human-attention protocol
- [`beads-parallel-grinding`](../beads-parallel-grinding/SKILL.md) — the
  concurrent variant, running several beads in isolated worktrees
- [`beads-blocker-review`](../beads-blocker-review/SKILL.md) — how the user
  drains the human queue this skill fills
