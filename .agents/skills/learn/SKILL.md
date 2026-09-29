---
name: learn
description: >-
  Pauses current work to root-cause one specific mistake the agent just made,
  such as not committing despite instructions to, by checking it against the
  loaded AGENTS.md, CLAUDE.md, skills, and Beads memories; proposes concrete
  context improvements, and lets the user choose which to apply and how to
  remediate. Use when the user invokes `/learn` or `$learn`, with or without
  a description of the mistake. For a broad end-of-session documentation
  sweep, use `documentation-updates` (`/reflect`) instead.
---

# Learn from a mistake

The user has interrupted ongoing work because you just made a mistake. Treat
this as an **interlude**: the only goal is to understand why the mistake
happened and stop it recurring.

## Boundary

Until the interlude ends, do nothing except the steps below. Do not resume
the paused task, and do not fix the mistake itself before the user has
chosen a remediation. Acting early would pre-empt the user's decision and
muddy the evidence you are examining.

## 1. Pin down the mistake

If the user described the mistake, use that. Otherwise infer it from the
recent turns, for example: uncommitted changes despite commit instructions,
a rule in loaded instructions that was ignored, or a question asked in plain
text instead of via the questionnaire tool. Confirm your guess with the
questionnaire tool (in Claude Code, `AskUserQuestion`), offering the most
likely candidates. If you cannot guess, ask the user what went wrong.

## 2. Investigate the cause

Find what the context said about this situation at the moment of the
mistake. Look at:

- the `AGENTS.md` / `CLAUDE.md` chain: global, project, and any nested
  directories involved;
- skills that were loaded, or should have been;
- Beads memories (`bd memories <keyword>`) and hook output such as
  `bd prime`;
- system reminders, output styles, and any other docs provided in the
  session.

Quote the relevant instructions with `path:line`. Then classify the cause.
Common ones:

- **Gap**: nothing covered the situation.
- **Contradiction**: two sources disagreed, e.g. a generic "do not commit
  unless authorised" default competing with a repository opt-in that grants
  commit authority.
- **Out of scope at decision time**: the rule lived in a skill or file that
  was not loaded when the decision was made, or was lost to compaction.
- **Ambiguous or weak wording**: the rule could reasonably be read as not
  applying, or was buried among louder instructions.
- **Rule present and clear, but not followed.**

Separate evidence from hypothesis. Your introspection into why you acted is
unreliable, so say "I don't know" rather than inventing a cause the context
does not support.

## 3. Propose improvements

Offer two to four concrete options. For each, name the target file, show the
proposed wording or diff, and say why it addresses the cause found. Prefer:

- resolving a contradiction over adding another rule on top of it;
- moving guidance to where it is in scope at the moment of decision, such as
  the skill used when finishing a task;
- mechanical enforcement (hooks, scripts, checks) over more prose, where
  feasible; and
- tightening existing wording over repeating it elsewhere.

Follow `documentation-updates` for choosing where a lesson belongs, and
respect repository rules about content, e.g. public repositories must not
receive private or author-specific material.

## 4. Ask the user

Use the questionnaire tool. Improvements come first as a multi-select with a
"none" option. Remediation comes last as a single choice listing the
plausible fixes for this mistake (e.g. commit now, revert, redo the step)
plus "no remediation". Both questions may go in one questionnaire call.

## 5. Apply and stop

Apply only what the user chose, verify it, and handle commits according to
the repository's policy. Report what changed, with a one-line reminder of
where the paused work stood. Then stop: resume the paused task only when the
user says so.
