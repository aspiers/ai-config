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

## Delegate steps 2 and 3 where possible

Hand steps 2 and 3 to a separate agent so the investigation does not fill
your context or block the user. Otherwise do them inline.

**Under Orca** (`ORCA_TERMINAL_HANDLE` is set), do not use a harness
subagent. Start a supervised Orca worker in a fresh tab instead, following
the `orchestration` skill and resolving the CLI as it says (on Linux,
`orca-ide`, never bare `orca`):

1. Pick the repository that owns the instruction files most likely at
   fault, e.g. the repo a skill resolves into (`realpath` its directory).
   Find its id and path with `repo list --json`. Use that main checkout,
   not a new worktree: steps 2 and 3 are read-only.
2. `orchestration run-create --objective "learn: <mistake>" --json`, then
   `orchestration worker-start --spec "<brief>" --worktree
   id:<repoId>::<path> --agent <your agent> --json`. Orca opens the tab,
   waits for the agent to be ready, and injects the brief along with the
   exact `worker_done` command to report back with.
3. Wait for the report with `orchestration check --wait --types
   worker_done,escalation,question --timeout-ms 900000 --json`, in the
   background where the harness allows. Then ack the delivery and
   `worker-release` the dispatch.

**Otherwise**, use a harness subagent, preferably in the background.
Prefer one that inherits this conversation, such as Claude Code's `fork`
subagent type, because the transcript is the main evidence.

An Orca worker or a fresh subagent sees nothing of this session, so its
brief must carry:

- the mistake as confirmed in step 1, in the user's words where possible;
- the transcript facts that matter: what was asked, what you did and when,
  and the decisions or commands involved;
- the instruction sources in play: `AGENTS.md` / `CLAUDE.md` paths,
  skills loaded or skipped, and the text of any system reminders, hook
  output, or other injected context that its tools cannot re-read;
- the repository's content rules, e.g. that it is public.

In every case, tell it to follow steps 2 and 3 of this skill read-only:
no edits, commits, or questions to the user. It should report the cause
with quoted evidence and the proposals with target files and exact wording;
an Orca worker writes the report to a file and passes it as
`--report-path`.

Then tell the user in one line that the investigation is running, and that
meanwhile you can continue the paused task if they say so. When the report
arrives, check that its quotes are real and its proposals follow step 3,
then go to step 4.

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

Present the proposals yourself, even when a subagent drafted them, and use
the questionnaire tool. Improvements come first as a multi-select with a
"none" option. Remediation comes last as a single choice listing the
plausible fixes for this mistake (e.g. commit now, revert, redo the step)
plus "no remediation". Both questions may go in one questionnaire call.

## 5. Apply and stop

Apply only what the user chose, verify it, and handle commits according to
the repository's policy. You may delegate the edits to a subagent, but
verify the result yourself. Report what changed, with a one-line reminder of
where the paused work stood. Then stop: resume the paused task only when the
user says so.
