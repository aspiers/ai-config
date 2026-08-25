---
name: tldr-summarise
description: >-
  Summarises the current session for a human who has not read it, or cannot
  remember it, and needs to get back up to speed fast. Use when the user asks
  for a TL;DR, a catch-up, a recap, or to be reminded where things got to,
  especially when they have been away or working in other sessions.
---

# TL;DR Summarise

Write a summary that swaps the reader's context back in.

Assume the reader is the human, that they have **not** read the preceding
output, and that they have been multi-tasking across unrelated sessions since
they last looked. Nothing earlier in the conversation is in their head. Their
memory of this work is cold, and the summary is what warms it.

## Length and shape

**Hard ceiling: 200 words.** Not a target. Most summaries should come in well
under it, and a session with little in it deserves three lines, not padding
up to the limit.

**Use headed sections of bullets — never paragraphs.** A returning reader
scans for the section they need and reads only that. Prose makes them read
from the top to find out whether anything concerns them.

The failure mode this guards against is a summary that is accurate,
well-organised, complete, and still useless because it takes as long to read
as scrolling back would have. If it cannot be absorbed in one pass at speed,
it has failed regardless of how good the content is.

Use this shape:

```markdown
## Sentence-case title: what this session is about

- One bullet of orientation, if the title needs it

## DONE

- What changed, with its ID

## LEARNED

- What turned out to be true that nobody knew before

## BLOCKED ON

- What is stopping the next step, and who it waits on

## NEXT

- The specific thing to pick up, and why it is that one

## RUNNING NOW

- Only when something actually is — omit the whole section otherwise

## NEEDED FROM YOU

- The honest answer, including "nothing"
```

Section labels are uppercase so they read as signposts rather than as more
prose; the title stays sentence case, because a long uppercase line is a
banner and is harder to read, not easier.

Every line is a bullet, including inside a section with only one. Consistency
is what makes the whole thing scannable — one prose paragraph in the middle
becomes a wall the eye has to stop and parse.

Keep bullets to one line each wherever possible. A bullet needing three
clauses is usually two bullets.

Drop any section with nothing true and material to put in it. An empty
heading is worse than no heading.

**DONE** comes first: it is the reader's anchor, and the rest is easier to
place once they know what actually changed.

**NEXT** is what makes the summary actionable rather than merely informative.
Name one concrete thing, not a menu: the actual candidate, why it is that one,
and what it depends on. "Resume the work" is not a next step. If the honest
answer is that nothing can proceed until a blocker clears, say that plainly —
it is a real answer, and it tells the reader to put this down.

Where the choice genuinely belongs to the reader, give the two or three real
candidates one bullet each, saying what turns on the choice, then stop.

**BLOCKED ON** must name who the blocker waits on, not just what it is.
"Blocked" alongside a **NEEDED FROM YOU** of "nothing" reads as a
contradiction unless the line says why it is not the reader — waiting on elapsed time, on a
scheduled run, on events that arrive during normal use, on another person. A
reader who cannot tell whether a blocker is theirs has to go and find out,
which is the work this summary exists to save.

**LEARNED** is the section most worth protecting. What was done is recoverable
from the commit log and the issue tracker; what was learned usually exists
nowhere but this conversation, and vanishes with it. It covers a root cause
found, an assumption disproved, a surprising behaviour discovered, a
correction to something believed earlier. Never drop it to save space — cut
detail from **DONE** instead, since that is what the reader can look up.

## What to cover

The title carries the orientation: what this session is about. Without that
anchor the rest has nothing to attach to.

Every section earns its place only if it is true and material. Dropping one
that does not apply is better than a heading over a line of filler.

The last two sections are what a returning reader needs before they can act.

**RUNNING NOW** appears only when unattended agentic work is genuinely in
flight — background commands, running subagents, watches, loops, scheduled or
queued work — and then says what it is doing and roughly when it should land.
When the session is idle, drop the section rather than reporting "nothing":
its absence *is* the answer, and a heading whose only content is the absence
of news costs the reader two lines to learn nothing.

That makes the omission load-bearing, so check before leaving it out. A reader
who cannot tell idle from stalled has to choose between interrupting work that
is progressing fine and waiting on work that stopped ages ago — and they will
now infer "idle" from silence.

**NEEDED FROM YOU** states whether the reader is currently the blocker, and if
so, exactly what is being asked: a decision, an approval, a credential,
something only they can observe or run. Name the ask and the command or choice
that answers it — enough to act on, not a briefing on the alternatives. If a
queue of these already exists, point at how to drain it rather than restating
its contents. This section always appears, because "nothing" is genuine
information and lets the reader put it down again.

**"Nothing" must mean nothing.** Do not write "nothing — just confirm X", or
append an approval, a decision, or a question to a section that opened by
saying nothing was needed. Confirming *is* something needed, and a reader who
trusts the first word and stops reading has just missed the ask.

Decide which it is, and commit:

- Something is genuinely wanted → name it, and do not dress it as nothing. One
  clear ask beats a soft one they skim past.
- Nothing is → say "Nothing", and put anything merely *available* to them
  under **NEXT**, where an unclaimed option belongs.

An optional next step is not a request; a pending approval is. The test is
whether work is actually stalled until they respond — if it is, that is an
ask, however lightly it is phrased.

Throughout, prefer what the reader cannot reconstruct: conclusions reached,
blockers hit, decisions made and their reasons. Skip the narrative of how the
work proceeded, and skip detail they can look up once they are oriented.

A correction or reversal is never optional — if something believed earlier
turned out wrong, say so plainly, even at the cost of a line elsewhere. A
reader acting on a stale mental model needs the correction more than they
need the conclusion.

## Naming things

Never refer to an entity by a bare identifier. Issue keys, bead IDs, PR and
ticket numbers, commit SHAs and file paths mean nothing to a cold reader, who
would have to look each one up to parse the sentence — the exact cost this
summary exists to avoid.

Give every reference a short human-readable label **and** keep its ID, since
the ID is what commands and searches take as an argument:

- `ai-1df (add a TL;DR summary skill)`
- `PR #4271 (fix race in worktree cleanup)`

This overlaps with the `/ids` command, which enforces the same rule for the
rest of a conversation. Here it is a property of the summary itself.

## Language

Use plain language a competent colleague would understand without having
followed this session. Expand or avoid jargon local to this context — tool
names, internal shorthand, abbreviations coined earlier in the conversation,
and project-specific terms the reader may not have loaded. Where a term is
genuinely needed, gloss it in passing rather than assuming recall.

The test: someone who has been thinking about something else entirely for
hours should be able to read it once, at speed, and come away knowing where
things stand, whether anything is still running without them, and whether
they are being asked for something right now.
