---
name: orca-cli-local
description: Applies local lessons to every use of the Orca CLI (orca-ide, orca-dev). Use alongside the upstream orca-cli skill whenever the Orca CLI is needed, including before creating a branch worktree or asking the user for feedback on a change before committing while running inside Orca.
---

# Local orca-cli guidance

Load the upstream `orca-cli` skill for the command surface, then apply these
rules to every Orca CLI command. Each one exists because the upstream
defaults or an agent's assumptions produced the wrong result: on 2026-09-17
(tacticalvote), a worktree with an idle shell instead of a working agent,
branched from a stale base; later, a coordinator that denied having a
message channel, and prompts typed into agents' dialogs.

## "Start this in a separate worktree" means an agent runs there

When the user asks for work to be started, done, or handed off in a new
worktree, they expect to watch an agent working in that worktree's terminal.
Doing the work from the current session while the new terminal sits idle is
the failure to avoid.

- Pass `--agent <id> --prompt "<full brief>"` in the same `worktree create`
  call. Default to `claude` unless the user names another agent.
- The brief must be self-contained: the original request verbatim, the PR
  target branch, and any repo constraints the current session already
  learned (test commands, hosting, files to look at). If the user tests
  through a `working` mixdown branch in that repo, say so and tell the
  worker to load `git-branch-management` before its first commit.
- After create, `terminal read` the returned agent handle and confirm the
  brief is visible before reporting the handoff as started.
- Only work in the new checkout from the current session if the user
  explicitly says so.

## Never trust the repo's configured base ref

Upstream says to omit `--base-branch` for independent work so Orca uses the
repo default base. That default is stored Orca config and drifts: for
tacticalvote it still pointed at `origin/locals-2025`, 211 commits behind
`origin/main`, the branch PRs actually target.

- Determine the PR target first (`gh repo view --json defaultBranchRef`,
  recent `gh pr list --json baseRefName`, or CLAUDE.md), then pass it with
  `--base-branch origin/<target>` explicitly.
- Read `baseRef` and `head` from the create result and check `head` equals
  `git rev-parse origin/<target>`. If not, remove the worktree
  (`worktree rm --force`, safe only while it has no changes) and recreate;
  do not rebase or `reset --hard` inside it.
- When the configured base is stale, fix it once with
  `repo set-base-ref --ref origin/<target>` and tell the user.

## Every new worktree gets its own agent

When running inside Orca (`ORCA_PANE_KEY` is set) in a repository with an
`orca.yaml`, or registered in Orca, create every new worktree with
`worktree create`, including one for your own next change. Outside Orca the
CLI cannot create one; follow `git-branch-management` instead.
`git worktree add` and `wt switch --create` skip Orca's setup, leaving no
dependencies or env files. Pass `--no-parent`, `--base-branch
origin/<target>` (see above), and `--setup run` unless the repository's
setup policy already runs it.

A new worktree exists so that a new agent can work in it, even when the
user only asked for the change and never mentioned a worktree, and even
when you are already an agent in another worktree. Pass `--agent` and a
self-contained `--prompt` in the same `worktree create` call, following the
handoff rules above, and do not edit, build or test in that worktree from
the current session. If you need its result, start a supervised worker
instead (see "Talking to agents you started"). The agent's start waits for
setup only when the repository sets `setupAgentStartupPolicy:
wait-for-setup`; otherwise tell it in the brief to check that setup has
finished first.

Work in the new worktree yourself only when the user explicitly says so.
Then, before editing, `terminal list --worktree <selector>` and `terminal
read` the setup terminal to confirm setup finished without errors.

## Handles go stale quickly

A `terminal wait` on the create-returned handle can report
`terminal_handle_stale` within a minute while the agent is in fact running.
Re-list terminals for the worktree and continue with the replacement handle;
do not treat the stale error as a failed handoff.

## Talking to agents you started

Orca has inter-agent messaging (`orchestration --help`). Never tell the user
that typing into a terminal is the only way to reach an agent.

Messaging is pull-only for plain handoff agents: Orca's hooks inject no
mail, so a recipient sees messages only when it runs
`orca-ide orchestration check`. Set the channel up in the initial
`--prompt` brief:

- the coordinator's handle (`$ORCA_TERMINAL_HANDLE`);
- "run `orca-ide orchestration check --terminal "$ORCA_TERMINAL_HANDLE"`
  at each checkpoint"; and
- "report with `orca-ide orchestration send --to <coordinator handle>
  --type status|question|escalation`".

Don't ask a plain handoff agent for `worker_done`; without a Dispatch it is
rejected ("worker_done requires taskId"). When you want reports or
supervision from the start, use supervised workers instead
(`orchestration run-create`, then `worker-start`; see the `orchestration`
skill).

When several agents work related beads in parallel, give each one's brief the
others' terminal handles and bead IDs, and tell it to:

- run `orca-ide orchestration send --to <handle>` whenever a finding unblocks
  or changes a sibling's bead, as well as commenting on that bead
  (`beads-best-practices`); and
- run `orca-ide orchestration check --terminal "$ORCA_TERMINAL_HANDLE"` while
  waiting on another bead, since messages are pull-only.

Supervised siblings in one Run can use the Run's group addresses instead
(`orchestration` reference `messaging-and-gates.md`).

## Offer Orca's diff view for review

When running inside Orca and you need the user's feedback on a change
before committing, never put it in a Markdown file for them to review.
Leave the edit uncommitted, and offer, as one option in your question, to
open each changed file in its own tab with `file diff <path> --worktree
<selector>`. Open the tabs only if the user picks that option. Showing the
change in chat through the harness's own diff display is also fine.

A diff tab shows every uncommitted change in that file, not only yours. If
the file also has hunks you didn't write, say so when you offer the tab, and
say which hunks are yours.

## Read the screen before every send

Before any `terminal send` to an agent, `terminal read` it. Send only if it
is idle at its normal input prompt: no dialog, menu, questionnaire,
permission prompt, running turn, or startup screen. `tui-idle` alone is not
enough; typed text and Enter can answer a dialog and change its settings.

Otherwise skip that terminal and report it to the user. After sending,
`terminal read` again to confirm the text arrived as a prompt.
