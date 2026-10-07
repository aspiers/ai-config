---
name: learn
description: >-
  Root-causes one specific mistake the agent just made, such as not
  committing despite instructions to, by checking it against the loaded
  AGENTS.md, CLAUDE.md, skills, and Beads memories, delegating the
  investigation to a separate agent where the harness supports one;
  proposes concrete context improvements, and lets the user choose which to
  apply and how to remediate. Use when the user invokes `/learn` or
  `$learn`, with or without a description of the mistake, including
  `/learn /qs`-style shorthand naming the corrective command. For a broad
  end-of-session documentation sweep, use `documentation-updates`
  (`/reflect`) instead.
---

# Learn from a mistake

The user has interrupted ongoing work because you just made a mistake. Treat
this as an **interlude**: the goal is to understand why the mistake happened
and stop it recurring, without derailing the task it interrupted any
further.

## Boundary

Until the user has chosen from your proposals:

- do not fix the mistake itself, and do not edit instructions, skills, or
  memories on the strength of the investigation. Acting early would pre-empt
  the user's decision and muddy the evidence being examined;
- do not resume the paused task on your own initiative. If the
  investigation runs in a separate agent, you may work on the paused
  task, but only as the user directs.

## 1. Pin down the mistake

If the user described the mistake, use that. Otherwise infer it from the
recent turns, for example: uncommitted changes despite commit instructions,
a rule in loaded instructions that was ignored, or a question asked in plain
text instead of via the questionnaire tool. Confirm your guess with the
questionnaire tool (in Claude Code, `AskUserQuestion`), offering the most
likely candidates. If you cannot guess, ask the user what went wrong.

If the argument names a slash command or skill (e.g. `/learn /qs` or
`/learn /ids`), the mistake is whatever that command corrects. Read its
`SKILL.md` or command file, restate the mistake from it in one line, and
skip confirming. The aim is that the user never needs to type that command
for this again.

## Delegate where possible

Hand the rest of the interlude to a separate agent so the investigation does
not fill your context or block the user. Otherwise do steps 2 to 5 inline.
Exactly one session asks the user the step 4 questions; asking them in two
places wastes the user's attention.

Before dispatching, write two one-line summaries: what `/learn` is meant to
address, and the task that was paused to invoke it. The outcome may arrive
long after the user has moved on, possibly after compaction, so capture them
now rather than reconstructing them later.

### In a visible pane, the delegate asks the user itself

If you are running inside an environment that can open a tab or pane and
start an agent in it, start the delegate there. The user can see it, so it
runs steps 2 to 5 itself, asking in its own pane and applying what they
choose. Use the first of these that applies:

- **Orca** (`ORCA_TERMINAL_HANDLE` is set): a new tab running your agent's
  CLI with the brief as its initial prompt, read from a file in that
  checkout's `tmp/`, and a session name (see below):

  ```sh
  orca-ide terminal create --worktree <selector> --title "<readable title>" \
    --command '<agent CLI> --name "<session name>" "$(cat tmp/<brief>.md)"'
  ```

  This is a handoff, not a supervised worker, so it needs no heartbeats,
  `worker_done` or release. Do not use a harness subagent. On Linux the CLI
  is `orca-ide`, never bare `orca`.
- **Herdr** (`HERDR_ENV=1`): a new pane with an agent started in it, as the
  `herdr` skill describes, given a session name the same way.
- **tmux** (`TMUX` is set): a new window running your agent's CLI, with the
  brief as its initial prompt and a session name the same way.

Name the session after the mistake in three to six words, with the agent's
launch flag (`claude --name`, `pi --name`); omit it for an agent without
one, such as Codex.

Start it in the main checkout of the repository that owns the instruction
files most likely at fault, e.g. the one a skill resolves into (`realpath`
its directory; under Orca, `repo list --json` gives its id). Follow that
repository's rules on where commits go.

Then tell the user in one line where the `/learn` questions will appear, and
that meanwhile you can continue the paused task if they say so. Do not
present or ask the proposals in your own session, even if the user raises
them there. Pass anything they tell you on to the delegate instead of
starting another agent.

Do not wait for it or relay its outcome: the user sees the questions and
results first-hand in the delegate's pane. Carry out the remediation the
user chose on the paused task only if they direct you to.

### Otherwise, a subagent investigates and you ask

Use a harness subagent for steps 2 and 3 only, preferably in the background.
Subagents cannot reliably put a question in front of the user, so you do
steps 4 and 5 yourself.

Prefer a subagent that inherits this conversation, such as Claude Code's
`fork` subagent type, because the transcript is the main evidence.

Tell the user in one line that the investigation is running, and that
meanwhile you can continue the paused task if they say so. When the report
arrives, check that its quotes are real and that its proposals follow
step 3, then go to step 4.

### The brief

A delegate that does not inherit this conversation sees nothing of it, so
its brief must carry:

- both summaries, which a delegate in a visible pane uses to open its step 4
  questions;
- the mistake as confirmed in step 1, in the user's words where possible;
- the transcript facts that matter: what was asked, what you did and when,
  and the decisions or commands involved;
- the instruction sources in play: `AGENTS.md` / `CLAUDE.md` paths,
  skills loaded or skipped, and the text of any system reminders, hook
  output, or other injected context that its tools cannot re-read;
- the repository's content rules, e.g. that it is public.

Tell a delegate in a visible pane to load this skill and follow steps 2 to 5.
Its brief must also tell it:

- to ask the user directly with its own questionnaire tool, in its own
  pane;
- to check its quotes before asking, since nobody else will;
- to apply, verify and commit only what the user chose, and to leave the
  paused task alone, because that task belongs to you;
- to end with the outcome: the cause, what was applied with commit SHAs, and
  the remediation the user chose. Write a report file only if the user
  asks for one.

Tell a subagent to follow steps 2 and 3 read-only: no edits, commits, or
questions to the user. It reports the cause with quoted evidence, and the
proposals with target files and exact wording.

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
receive private or author-specific material. Lessons are agent-agnostic by
default: target sources every agent reads, such as `AGENTS.md`, the shared
global rules file, or a skill. Name an agent-specific file, such as
`CLAUDE.md`, only for that agent's own features, and say why.

## 4. Ask the user

When the investigation was delegated, the user has probably lost track of
why it started. Open the findings by re-anchoring them, using the two
summaries from dispatch:

> Here are the findings from `/learn` on [what it was meant to address],
> which you invoked while working on [the paused task]:

Then give the cause and evidence. Present the proposals yourself, even when
a subagent drafted them, and use the questionnaire tool. Ask one question
per proposal, never one multi-select covering them all. Each question must
stand alone: say what the change is, where it goes, and what it fixes, so
the user can answer without remembering earlier context. Remediation comes
last, as a single choice listing the plausible fixes for this mistake (e.g.
commit now, revert, redo the step) plus "no remediation".

## 5. Apply and stop

Apply only what the user chose, verify it, and handle commits according to
the repository's policy. You may delegate the edits to a subagent, but
verify the result yourself. Report what changed, with a one-line reminder of
where the paused work stood. Then stop: resume the paused task only when the
user says so.
