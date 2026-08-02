---
name: git-commit
description: Review staged changes and create atomic Git commits whose messages match repository conventions. Use when the user asks to commit, write a commit message, or finalize already staged work.
---

# Git Commit

Create a commit that accurately describes one logical staged change.

## Respect the index boundary

Treat the staging area as user-controlled input. Do not stage, unstage, or
otherwise alter it unless the user explicitly asks for that operation. Use the
`git-staging` skill when selective staging is requested.

If nothing is staged, report that fact and ask whether the user wants help
staging. If staged and unstaged changes coexist, keep them distinct throughout
the review.

## Workflow

1. Inspect `git status`, `git diff --cached --no-ext-diff`, and enough recent
   history to learn the repository's message style.
2. Confirm the staged diff is coherent and contains no apparent secrets,
   accidental files, or unrelated changes.
3. If the staged content combines independent concerns, explain the split and
   ask before changing the index. Otherwise continue without inventing extra
   commits merely because several files changed.
4. Write a message that emphasizes why the change exists and accurately
   summarizes the staged diff.
5. Commit, then verify the resulting commit and remaining working-tree state.

## Message guidance

Follow repository conventions first. Use Conventional Commits only when the
history or project rules use them. Keep the subject concise and imperative
when that matches local style; add a body when rationale, behavior changes, or
migration details would help future readers.

Include issue references, task files, sign-offs, or AI attribution only when
relevant or required by the repository or user. Do not fabricate metadata.

Before reporting success, inspect the created commit (for example with
`git show --stat --oneline HEAD`) and state what remains uncommitted.
