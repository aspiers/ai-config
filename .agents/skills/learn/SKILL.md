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
  `/learn /qs`-style shorthand naming the corrective command. Also use
  unprompted as soon as the agent admits a mistake of its own, or is about
  to propose changing instructions, skills, or memories because of one,
  instead of making or recommending that edit directly. For a broad
  end-of-session documentation sweep, use `documentation-updates`
  (`/reflect`) instead.
---

# Learn from a mistake

You just made a mistake. Either the user interrupted ongoing work to invoke
this, or you admitted the mistake yourself. Treat this as an
**interlude**: the goal is to understand why the mistake happened and stop
it recurring, without derailing the task it interrupted any further.

## Boundary

Until the user has chosen from your proposals:

- do not fix the mistake itself, and do not edit instructions, skills, or
  memories on the strength of the investigation, except as the uncommitted
  drafts step 4 opens for review. Acting early would pre-empt the user's
  decision and muddy the evidence being examined;
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
address, and the task that was paused to invoke it. Each names the
repository or project its work is in, since the delegate may run in
another. The outcome may arrive long after the user has moved on, possibly
after compaction, so capture them now rather than reconstructing them later.

### In a visible pane, the delegate asks the user itself

If you are running inside an environment that can open a tab or pane and
start an agent in it, start the delegate there. The user can see it, so it
runs steps 2 to 5 itself, asking in its own pane and applying what they
choose. Use the first of these that applies:

- **Orca** (`ORCA_TERMINAL_HANDLE` is set): a new worktree workspace with
  your agent started in it, so each `/learn` shows in Orca's sidebar. Write
  the brief to a file in your own repository's `tmp/` first:

  ```sh
  orca-ide worktree create --repo path:<main checkout> --name <slug> \
    --parent-worktree path:<main checkout> --base-branch <trunk> \
    --setup run --agent <agent id> --prompt "$(cat tmp/<brief>.md)"
  ```

  `<slug>` is the session name's first three to six words, slugified; it
  labels the sidebar row. `--agent` cannot pass `--name` yet
  ([`stablyai/orca#25067`][orca-25067]). Where the repository commits
  straight to its trunk, `<trunk>` is the local branch, which may be ahead
  of its remote.

  This is a handoff, not a supervised worker, so it needs no heartbeats,
  `worker_done` or release. Do not use a harness subagent. On Linux the CLI
  is `orca-ide`, never bare `orca`.
- **Herdr** (`HERDR_ENV=1`): a new pane with an agent started in it, as the
  `herdr` skill describes, given a session name the same way.
- **tmux** (`TMUX` is set): a new window running your agent's CLI, with the
  brief as its initial prompt and a session name the same way.

Name the session after the mistake in 8 to 12 words, most identifying
first, as `orca-cli-local` describes, with the agent's launch flag
(`claude --name`, `pi --name`); omit it for an agent without one, such as
Codex.

Start it in the repository that owns the instruction files most likely at
fault, e.g. the one a skill resolves into (`realpath` its directory; its
main checkout is the first entry of `git worktree list`). Follow that
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
- the instruction sources in play: absolute `AGENTS.md` / `CLAUDE.md` paths,
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

Under Orca, where the repository commits straight to its trunk, the brief
also tells the delegate how to get its branch merged. A repository that
takes PRs follows its own rules instead.

1. After committing, list agent terminals in the main checkout:
   `orca-ide terminal list --worktree path:<main checkout> --json`, keeping
   those whose `agentIdentity` is non-null.
2. If there is exactly one, it is the coordinator. Send it
   `orca-ide orchestration send --to <handle> --type question` with a
   subject `Merge <branch> into <trunk>` and the commits in the body, then
   follow `orca-cli-local` "Asking your coordinator to act".
3. If there are none or several, or no reply comes within 10 minutes, ask
   the user with the questionnaire tool: pick a coordinator, or let the
   delegate rebase onto the trunk and run `git -C <main checkout> merge
   --ff-only <branch>` itself.

A coordinator that merges cleans up the workspace as `orca-cli-local`
"Cleaning up after a handoff agent's branch merges" says. A delegate that
merged itself must not, since removing its own workspace kills it
mid-step: it tells the user the workspace is ready for removal.

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
> which you invoked while working on [the paused task] in [its repository
> or project]:

Then give the cause and evidence. Name the repository of every path you
mention, such as "ai-config's `.agents/AGENTS.md`", whenever the session's
repository differs from the paused task's. Present the proposals yourself,
even when a subagent drafted them, and use the questionnaire tool. Ask one
question per proposal, never one multi-select covering them all. Each question
must stand alone: say what the change is, where it goes, and what it fixes, so
the user can answer without remembering earlier context. Remediation comes
last, as a single choice listing the plausible fixes for this mistake (e.g.
commit now, revert, redo the step) plus "no remediation".

Inside Orca, before asking, apply each proposed change to a Markdown file
as an uncommitted edit and open each changed file's diff in its own tab,
as `orca-cli-local` describes. Revert the edits the user declines.
Elsewhere, show the proposed wording or diff in chat.

## 5. Apply and stop

Apply only what the user chose, verify it, and handle commits according to
the repository's policy. You may delegate the edits to a subagent, but
verify the result yourself. Report what changed, with a one-line reminder of
where the paused work stood. Then stop: resume the paused task only when the
user says so.

[orca-25067]: https://github.com/stablyai/orca/issues/25067
