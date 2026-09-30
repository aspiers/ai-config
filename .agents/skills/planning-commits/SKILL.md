---
name: planning-commits
description: >-
  Triages an already-dirty Git working tree: breaks down every uncommitted
  change hunk by hunk, separates deliberate edits from tool-written churn,
  possibly accidental reversions, misplaced scope, and sensitive content,
  asks the user about the ambiguous cases, and proposes an ordered set of
  commits plus a list of hunks to hold back. Use when the user invokes `/pc`
  or `$pc`, asks what they should commit, wants their uncommitted changes
  broken down, or wants commits proposed for a dirty working tree or pile of
  accumulated local modifications. To plan commit boundaries for a change
  before or while implementing it, use `incremental-commits` instead.
---

# Planning Commits for a Dirty Working Tree

Turn an accumulation of uncommitted changes, often from several sessions,
people, or tools, into a plan of commits the user can approve.

## Boundary

Do not stage, commit, revert, discard, or delete anything until the user
approves the plan. The working tree may be the only copy of some changes, and
several of the classifications below are judgements the user must confirm.

## 1. Gather everything

- `git status --short --untracked-files=all`
- `git diff --no-ext-diff` and `git diff --no-ext-diff --cached`; keep
  already-staged changes distinct, since the index may be a boundary the user
  chose deliberately
- the contents of untracked files; say which ones you skipped as build
  output or binaries

Do not truncate output carelessly: a hunk that was never read cannot be
classified. For large diffs, save the output to a file and read it in parts.

## 2. Get context

- Run `git log` on the touched paths to learn the commit-message conventions
  and to see whether a change continues earlier work. For example, a new hook
  entry of the same kind that a recent commit added for other events belongs
  with that theme, and may even be a fixup of an unpublished commit.
- Read the repository's instructions (`AGENTS.md`, `CLAUDE.md`,
  `CONTRIBUTING`, and similar) for commit conventions and content rules.
- Establish whether the repository is public, from its instructions or its
  remote (e.g. `gh repo view --json visibility`). If you cannot tell, treat
  it as public.

## 3. Classify every hunk

Classify hunks, not files: one config file often mixes a deliberate setting
with tool noise.

- **Deliberate**: a change the user made on purpose. Group these by logical
  concern.
- **Tool-written state or churn**: an application rewriting its own config,
  such as auto-appended entries, trust or approval hashes, key reordering,
  version-specific path bumps, UI counters, "seen" or "done" flags, and
  timestamps. When a tool persists machine state into a version-controlled
  file, say so explicitly: it will recur until the root cause is fixed.
- **Possibly accidental**: a setting silently removed or reverted to an older
  value, a duplicate key cleaned up, unrelated lines reformatted. Ask rather
  than assume either way.
- **Misplaced scope**: content in the wrong file, such as project-specific
  settings landing in a global or user-level config, or machine-local paths
  in shared config. Propose where it belongs.
- **Sensitive or private**: credentials, tokens, personal data, private paths
  or project names, conversation or session titles, and anything the
  repository's instructions forbid. Never propose committing these. Apply the
  strictest reading in a public repository, because history is permanent; a
  credential that was already pushed must be rotated, not merely removed.

When a hunk fits several categories, such as tool-written state that also
leaks a private project name, report the most restrictive one.

## 4. Ask about the genuine decisions

Batch the decisions only the user can make into the interactive
questionnaire tool (`AskUserQuestion` in Claude Code, or the equivalent in
other harnesses), up to four questions per call, with the recommended option
first. Do not bury questions in prose, and do not ask about anything the
evidence already settles. Typical decisions: keep or revert a possibly
accidental change, where misplaced content should live, whether churn should
be reverted or left dirty, and whether two related concerns share a commit.

## 5. Present the plan

1. **Breakdown by file**: each file's hunks with their classification.
2. **Proposed commits**, in order: a message following the repository's
   conventions, and exactly which files and hunks each commit contains. Use
   `incremental-commits` for judgement on where to split and how to order.
3. **Hold back or revert**: each excluded hunk with its reason, and whether
   to revert it, leave it uncommitted, or move it elsewhere.
4. **Follow-ups**: for recurring churn, offer to investigate how to stop the
   tool writing it (a setting, an untracked local override file, an ignore
   rule) or to file an issue in the repository's tracker.

## 6. Execute after approval

Carry out the approved plan one logical commit at a time: stage exactly that
commit's hunks with `git-staging`, commit with `git-commit`, then check that
the remaining diff still matches the plan. Revert only the hunks the user
approved reverting. If a file changes during execution, for example because
a tool rewrote it again, stop and re-triage that file instead of committing
the new content.
