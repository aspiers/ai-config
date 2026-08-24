---
name: beads-blocker-review
description: >-
  Review every Beads issue waiting on a person, one at a time, using the
  interactive questionnaire UI rather than plain-text prompts. Use when asked
  to go through blockers, clear the human queue, answer beads waiting on the
  user, triage `bd human list`, or unblock agent work that needs a decision.
---

# Beads Blocker Review

Clear the queue of Beads issues waiting on a person, one at a time, asking
each question through the interactive questionnaire tool.

## When to Use This Skill

Use this skill when the user asks to:

- Go through blockers, or clear the human queue
- Answer beads that are waiting on them
- Triage `bd human list`
- Unblock agent work that stalled on a decision

## What Is In the Queue

Two mechanisms park work on a person, and they do not overlap. Check both.

1. **Beads labelled `human`** — listed by `bd human list`. This is the main
   queue and where nearly everything will be.
2. **Open human gates** — `bd gate list` shows open gates; the human ones are
   those of type `human`, which resolve only by hand. A gate blocks another
   bead until someone resolves it. Gates do **not** carry the `human` label,
   so they never appear in `bd human list`; checking only the first queue
   misses them silently.

Do not widen the sweep to `bd blocked`. Ordinary dependency blockers are
agent-resolvable work, not questions for the user.

## Record the Answer, Don't Do the Work

Recording the user's answer is the whole job. For each blocker: ask, record,
move on.

Do **not** implement what the answer implies, even when the change looks
small. The user invoked this to drain a decision queue in one pass, and
stopping to write code after every answer defeats that.

This works because a bead waiting on a person contains **only** their part —
the dependent agent work lives in its own bead. Answering releases that work
to be picked up later, by a grind or by you in a separate session.

If you meet a bead that mixes the two — the person's part and agent work in
one issue — say so when you report. It should have been split, and answering
it will close work nobody did.

## Workflow

1. **Inventory both queues.**

   ```bash
   bd human list --json
   bd gate list
   ```

   If both are empty, say so and stop. Do not go hunting for other work.

2. **Report the total up front** so the user knows how many questions are
   coming — e.g. "7 beads and 1 gate waiting on you."

3. **For each item, in priority order** (P0 first), repeat steps 4-7.

4. **Read it fully**, including comments — the question is often in a comment
   rather than the description:

   ```bash
   bd show "$id"
   bd comments "$id"
   ```

   Also note what depends on it, so you can tell the user what their answer
   will release. Note the direction: `up` shows what this bead blocks, which
   is what you want here — the default `down` shows the opposite.

   ```bash
   bd dep tree "$id" --direction=up
   ```

5. **Summarise the decision** in a few lines before asking: what the bead is,
   why it is waiting, and what turns on the answer. Always name a bead as
   `<id> (<title>)`, never by bare ID.

6. **Ask using the questionnaire tool**, one bead per call:

   - Claude Code: `AskUserQuestion`
   - OpenCode: the interactive questionnaire tool
   - Pi: `ask_user`

   Derive the options from the bead itself — its "Alternatives Considered"
   section, the comment posing the question, or the genuine choices the work
   presents. Give 2-4 concrete, mutually exclusive options with descriptions
   that state the consequence of picking each. If you have a recommendation,
   make it the first option and append "(Recommended)" to its label.

   Never batch several beads into one call. One bead, one call — that is what
   makes the review legible.

   If a question is genuinely open-ended (naming, free-form text), ask in
   prose for that one bead. Think hard before concluding it is open-ended;
   most "open" questions have 2-4 obvious candidates.

7. **Record the answer immediately**, before moving on.

   For a labelled bead:

   ```bash
   bd human respond "$id" --response "<the decision, plus rationale>"
   ```

   This adds the response as a comment and closes the bead with reason
   "Responded", which releases anything that depended on it. The `human`
   label stays attached — that is deliberate, and `bd human stats` reads it.

   If the answer makes the bead moot rather than deciding it:

   ```bash
   bd human dismiss "$id" --reason "<why it no longer applies>"
   ```

   For a gate, resolve it instead:

   ```bash
   bd gate resolve "$gate-id" --reason "<the decision>"
   ```

   Write the response so a reader six months from now understands it without
   this conversation: the decision, the reason, and the rejected option.

8. **Summarise at the end**: how many were answered, dismissed, or skipped;
   **which beads are now unblocked and ready for agent work**; and any
   follow-up work the answers created.

   That middle item is the point of the exercise — the user wants to know
   what they just released, not merely that the queue is empty.

## Handling Interruption

The user may bail out partway through, or answer with something that changes
the rest of the queue. Both are fine.

Because each answer is recorded before the next question is asked, stopping
early loses nothing. If the user stops, summarise what was cleared and what
remains, and do not press on.

If an answer to one bead obviously settles a later one, still ask about the
later bead — but say what the earlier answer implies and offer that as the
first option.

## Rules

- **Never answer on the user's behalf.** Do not call `bd human respond`,
  `bd human dismiss`, or `bd gate resolve` with a decision you invented. If
  you cannot construct sensible options, ask in prose rather than guessing.
- **Never skip an item silently.** If one cannot be asked about, say why.
- **Verify before recording.** Only record what the user actually chose,
  including any free text they added to their selection.
- **Re-read both queues if the session is long.** Items can be added or
  closed while the review runs; check again before declaring them empty.

## Verification

```bash
bd human list          # empty, or only the beads that were skipped
bd gate list           # no open human gates left
bd human stats         # responded and dismissed counts
bd ready               # work released by the answers
```

## Related Skills

- [`beads-best-practices`](../beads-best-practices/SKILL.md) — how beads
  reach this queue, and the one-bead-one-doer rule that keeps them answerable
- [`beads-grinding`](../beads-grinding/SKILL.md) — the serial grind that
  fills this queue and consumes the work it releases
- [`beads`](../beads/SKILL.md) — general Beads workflow
