---
name: orca-cli-local
description: Applies local lessons to every Orca worktree creation and agent handoff done through the orca CLI (orca-ide, orca-dev). Use alongside the upstream orca-cli skill whenever the user asks to start, do, or hand off work in a separate or new Orca worktree, spawn an agent in a worktree, or open a PR from one.
---

# Local orca-cli guidance

Load the upstream `orca-cli` skill for the command surface, then apply these
rules. They exist because the upstream defaults produced the wrong result on
2026-09-17 (tacticalvote): a worktree with an idle shell instead of a working
agent, branched from a stale base.

## "Start this in a separate worktree" means an agent runs there

When the user asks for work to be started, done, or handed off in a new
worktree, they expect to watch an agent working in that worktree's terminal.
Doing the work from the current session while the new terminal sits idle is
the failure to avoid.

- Pass `--agent <id> --prompt "<full brief>"` in the same `worktree create`
  call. Default to `claude` unless the user names another agent.
- The brief must be self-contained: the original request verbatim, the PR
  target branch, and any repo constraints the current session already
  learned (test commands, hosting, files to look at).
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

## Handles go stale quickly

A `terminal wait` on the create-returned handle can report
`terminal_handle_stale` within a minute while the agent is in fact running.
Re-list terminals for the worktree and continue with the replacement handle;
do not treat the stale error as a failed handoff.
