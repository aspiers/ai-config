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

Keep it to **at most 3-4 paragraphs**. Prose carries continuity and causation
better than fragments, so it usually suits the orientation the reader needs.
Reach for a short bullet list where the content is genuinely a list — several
parallel items, open decisions, or things waiting on the reader — since
flattening those into a sentence hides them. Let the shape follow the
content; just keep the whole thing inside the length budget.

## What to cover

Lead with orientation: what this session is about and why it was started.
Without that anchor the rest has nothing to attach to. Then cover where things
actually stand — what is done, what is in progress, and what was learned that
changed the direction.

Close on the two things a returning reader needs before they can act, and be
explicit about both wherever they apply.

**Is anything still running?** Say plainly whether unattended agentic work is
in flight — background commands, running subagents, watches, loops, scheduled
or queued work — and if so what it is doing and roughly when it should land.
Say so just as plainly when nothing is running and the session is idle. A
reader who cannot tell the difference has to choose between interrupting work
that is progressing fine and waiting on work that stopped ages ago.

**Is anything needed from them?** State whether the reader is currently the
blocker, and if so, exactly what is being asked: a decision, an approval, a
credential, something only they can observe or run. Give the real options and
what turns on each, so the ask is answerable from the summary alone. If a
queue of these already exists, point at how to drain it rather than only
counting it. Where nothing is needed, say that too — "nothing needed from you
right now" is genuine information, and lets them put it down again.

Prefer what the reader cannot reconstruct: conclusions reached, blockers hit,
decisions made and their reasons. Skip the narrative of how the work
proceeded, and skip detail they can look up once they are oriented.

If a correction or reversal happened — something believed earlier turned out
wrong — say so plainly. A reader working from a stale mental model needs the
correction more than the conclusion.

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
