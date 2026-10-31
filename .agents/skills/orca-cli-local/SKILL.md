---
name: orca-cli-local
description: Applies local lessons to every use of the Orca CLI (orca-ide, orca-dev). Use alongside the upstream orca-cli skill whenever the Orca CLI is needed, including before creating a branch worktree, when starting a fix or change in a repository registered in Orca, asking the user for feedback on a change before committing while running inside Orca, or reading review notes the user left on a file in Orca.
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
  worker to load `git-branch-management` before its first commit, and to
  ask you to remix rather than run or merely report one.
- Open every brief you write for another agent, however you start it, by
  saying who sent it and what the user asked for, e.g. "This brief comes
  from the coordinator agent, not the user. The user asked for: <their
  words, or nothing; the coordinator started this>." The receiving agent
  sees the brief as a user message, and this line is all that tells it
  otherwise. Grant only authority the user gave for this work: never
  write push, post or merge permission into a brief for work they did not
  ask for.
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
`worktree create`, including one for your own next change, and one for a
fix you were just asked to make, before diagnosing it. Outside Orca the CLI
cannot create one; follow `git-branch-management` instead.
`git worktree add` and `wt switch --create` skip Orca's setup, leaving no
dependencies or env files. Pass `--parent-worktree path:<main checkout>`,
`--base-branch origin/<target>` (see above), and `--setup run` unless the
repository's setup policy already runs it.

The parent keeps a repository's agent workspaces nested under its main
checkout in Orca's sidebar. The main checkout is the first entry of `git
worktree list`. Name it explicitly. If you omit it, Orca nests the new
worktree under whichever worktree you are running in, often an unrelated
feature.
Parent a stacked branch on the worktree of the branch it builds on instead.
Never pass `--no-parent`; the user repairs every such workspace by hand.

Don't try to group agents as tabs of one workspace by running them in
other worktrees from there. Orca ties a tab to its workspace's path, not the
shell's directory, so resume after Sleep or a restart, the diff and git
panels, and the agent's `active` selectors would all target the wrong
checkout.

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

## Name every agent you start

Give each agent session you start a name for its task, so it is
recognisable in the agent's session picker and in Orca. Titles come in
three tiers, each for a different width:

- **Long**, 8–12 words, most identifying words first: the session name,
  shown by `/resume` and in window titles.
- **Short**, 3–6 words and at most 40 characters: Orca's tab bar and
  Activity sidebar.
- **Tiny**, 1–2 words: narrow labels such as Herdr tabs.

Orca shows a tab's name on several surfaces, and each picks from different
fields:

- The tab bar uses the tab's custom title. Without one, it uses the
  agent's session name (Claude and Codex only), then the first prompt's
  opening words if "Auto-generate tab titles" is on, then the live
  terminal title.
- The Activity sidebar uses the custom title, else the opening words of
  the latest prompt. It never shows the session name.
- `terminal list` and `terminal show` report the latest terminal title,
  not what the tab bar shows.

So:

- With `terminal create --command`, put the long name on the agent's
  command line: `claude --name "<name>" …` or `pi --name "<name>" …`.
- Where a title-sync hook runs, it pins the short tier as the tab's custom
  title, using the name's leading words, and re-pins after every rename.
  Don't also pass `--title`: the hook replaces it. This repository's
  `pi-orca-tab-title` Pi extension is one such hook.

  > **⚠️ AUTHOR-SPECIFIC:** the author also runs a Claude hook,
  > `herdr-claude-title-watch` from their herdr-config repository, that
  > does the same for Claude in Orca, Herdr and tmux.

- Without a hook, and for Codex, which has no launch-time name flag, pass
  `terminal create --title "<short>"`. It pins the label everywhere until
  `terminal rename --terminal <handle>` without `--title` clears it, so it
  won't follow a later rename.
- `worktree create --agent` cannot pass agent arguments until
  [`stablyai/orca#25067`][orca-25067] lands, so those sessions get an
  automatically generated name, whose tiers a title-sync hook still pins.
  Don't abandon `--agent` just to name one.

[orca-25067]: https://github.com/stablyai/orca/issues/25067

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

Treat a remix request as work: run it in the main checkout one at a time,
rebuild and restart, then reply. While agents you started are still
working, run `orca-ide orchestration check --terminal
"$ORCA_TERMINAL_HANDLE"` before ending each turn, then arm a wait for their
next report, since nothing delivers their mail to you while you sit idle.
Start `orca-ide orchestration check --terminal "$ORCA_TERMINAL_HANDLE"
--wait --timeout-ms 3600000` as a background command your harness wakes you
on when it exits (in Claude Code, Bash with `run_in_background`). It exits
as soon as a message arrives and prints it; after an empty timeout, re-arm
it while agents are still working. Never ask the user to tell you to check:
on 2026-10-31 a finished branch sat unmerged until the user asked why. Only
if your harness cannot wake you, say that reports wait unread until the next
prompt.

The mailbox lives only as long as your
terminal, so clear pending requests before moving that terminal to
unrelated work.

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

## Asking your coordinator to act

A handoff agent that needs the agent that started it to act, for example
to remix, sends the request with `orchestration send`. The coordinator sees
it only when it next runs `orchestration check`, and an agent idle at its
prompt never does: on 2026-10-24 a remix request sat unread for 31 hours
while the worker reported it as asked. After sending:

1. `terminal read` the coordinator. If it is idle at its normal input
   prompt (see "Read the screen before every send"), `terminal send` it a
   one-line prompt naming the request's subject and asking it to run
   `orca-ide orchestration check --terminal "$ORCA_TERMINAL_HANDLE"`. If it
   is busy, leave it.
2. Wait for the reply with `orca-ide orchestration check --terminal
   "$ORCA_TERMINAL_HANDLE" --wait --timeout-ms 600000`.
3. Report the request as pending until the reply arrives, never as done. If
   the wait times out, run `orca-ide orchestration inbox --terminal
   <coordinator handle> --json`. `read: 0` means nobody has seen it: tell
   the user and name the coordinator's terminal.

Supervised Dispatch workers use their preamble's `ask` instead.

## Cleaning up after a handoff agent's branch merges

Merging a handoff agent's branch does not end the agent or remove its
workspace, and telling it to stop does neither: agents have gone on
committing after "you can stop". Supervised workers have `worker-release`
(see the `orchestration` skill); plain handoff agents need this instead.
Do it for each agent as soon as its branch has merged into the trunk, not
at the end of the session:

1. Check the work has fully landed: `git cherry <trunk> <branch>` prints
   no `+` lines and `git -C <worktree> status --short` prints nothing.
2. `terminal read` the agent. Go on only if it is idle at its input
   prompt and has reported nothing since you merged. If it is mid-turn,
   has started other work, or started agents of its own, leave the
   workspace and tell the user.
3. Close its terminals and remove the workspace through Orca, so Orca's
   sidebar and resume records stay consistent:

   ```sh
   orca-ide terminal close --worktree <selector> --all
   orca-ide worktree rm --worktree <selector>
   ```

   Without `--force`, `worktree rm` refuses a dirty worktree. It deletes
   the branch when Orca can prove it merged; otherwise check with `git
   cherry` and run `git branch -d <branch>`. Add `--run-hooks` when the
   repository defines an archive hook. It can return `removing: true`
   before git has finished, so confirm with `git worktree list`.
4. If the branch was pushed, delete the remote copy only where you may
   push; otherwise list it for the user.

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

This is about code changes. A Markdown draft of text to publish, such as a
PR body, goes in an Orca tab instead, as described next, and so does a
report, spec or design written for the user to read.

## Markdown for the user to read or review

Open any Markdown file you write for the user to read or review in an Orca
editor tab, in the same turn and before asking about it:

```sh
orca-ide file open <path>
```

Committing the file or summarising it in chat does not replace opening it.

Write any Markdown draft the user must review before it is sent or
published, such as a PR title and body, an issue or a comment, to a file
in the repository's `tmp/` and open it the same way. Name the path in your
message instead of pasting the draft. Plain-text drafts and bead text stay
as they are.

## Reading the user's review notes

The user can leave review notes on lines of a file in Orca's editor or
diff view. Orca keeps them in its own data, not in the file or in git, so
`git diff` shows nothing. Read them with:

```sh
orca-ide worktree show --worktree <selector> --json |
  jq '.result.worktree.diffComments'
```

Each note has `filePath`, `startLine` and `lineNumber` (an inclusive
range), `selectedText` and `body`. They are not the worktree's `comment`
field, which is the status line on the workspace card. Orca's Send action
removes the notes it delivers, so an empty list may mean they were already
sent to an agent.

Apply each note to its selected text and the problem its body names.
Keep the rest of the passage, its facts and lists included, even when that
makes the reword harder, and ask before removing anything the note didn't
mention.

Orca anchors a note only by its stored line numbers and selected text and
never updates them when the file changes. Save the notes to a file in
`tmp/` before editing or renaming the file they annotate: edits can move a
highlight to another match of the same words or drop it, and a rename
leaves the notes pointing at the old path.

## Showing a page or HTML file to the user

`file open` opens an editor tab, which shows HTML as source. Open a rendered
page, such as an HTML report, in Orca's built-in browser:

```sh
orca-ide tab create --url "file://$(realpath <file>)" --json
```

Confirm it loaded with `tab show --page <id>`, passing
`result.browserPageId` from the create output (not its top-level `id`); it
reports the title and URL. Write the file as a full document with
`<!doctype html>` and a charset meta, or it renders in quirks mode.

## Workaround: worker tabs titled `worker-task_<id>`

Temporary, until [`stablyai/orca#21917`][orca-21917] is fixed (seen in
1.4.219). `orchestration worker-start` stores `worker-<task id>` as the
custom title of each worker terminal it creates. A custom title outranks
Orca's task-derived title and the agent's own title, so the tab stays
unreadable whatever `--task-title` says.

Pass a readable `--task-title` to `worker-start`. Then, if it created a
terminal (no `--terminal`), clear the placeholder so the tab shows that
task title:

```sh
orca-ide terminal rename --terminal <worker handle>
```

The handle is `worker.agentTerminalHandle` in `orchestration worker-show
--dispatch <id> --json`. Omitting `--title` only removes the placeholder;
setting one would pin it over every later title. Workers without a terminal
need nothing.

[orca-21917]: https://github.com/stablyai/orca/issues/21917

## Workaround: Orca narrows fork remotes, hiding fork PRs

Temporary, until [`stablyai/orca#25703`][orca-25703] and
[`#12956`][orca-12956] are fixed (seen in 1.4.219). When a worktree's PR
comes from a fork, Orca reuses any remote with the fork's URL, including one
the user added, and replaces its `+refs/heads/*` fetch refspec with one for
that worktree's branch only. Other branches pushed to that remote then get no
tracking ref, and Orca shows no PR for them.

The `git-restore-fork-fetch-refspec` pre-push hook in this repository's
`bin/` repairs this on every push; its header shows how to install it
globally. `git hook list pre-push` shows `fork-fetch-refspec` when it is
installed.

Without the hook, after pushing a worktree's branch to a remote other than
`origin`, run `git for-each-ref --format='%(upstream)' refs/heads/<branch>`.
If it prints nothing, tell the user, and ask before running
`git config --add remote.<name>.fetch '+refs/heads/*:refs/remotes/<name>/*'`.
Leave Orca's per-branch lines in place. Orca still strips the wide line again
when a new fork-PR worktree on another branch is set up.

[orca-25703]: https://github.com/stablyai/orca/issues/25703
[orca-12956]: https://github.com/stablyai/orca/issues/12956

## Read the screen before every send

Before any `terminal send` to an agent, `terminal read` it. Send only if it
is idle at its normal input prompt: no dialog, menu, questionnaire,
permission prompt, running turn, or startup screen. `tui-idle` alone is not
enough; typed text and Enter can answer a dialog and change its settings.

Otherwise skip that terminal and report it to the user. After sending,
`terminal read` again to confirm the text arrived as a prompt.
