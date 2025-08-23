---
description: Stage relevant changes via git add
permission:
  bash:
    "git add": "allow"
    "git status": "allow"
---
# Staging Changes

Stage relevant changes via `git add`, taking great care not to add
unrelated files or changes.

## ⚠️ CRITICAL: Check for staged changes FIRST

Before any git operations, verify nothing is staged. If staged changes
exist, STOP and ask for permission.

## Context

- Current git worktree status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff --no-ext-diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`

## Process

1. Run `git status` to check for any already staged changes.
   **MANDATORY HALT**: If ANY files are already staged, you MUST stop
   immediately and ask the user for explicit permission before
   proceeding with any git operations.

2. Verify no staged changes exist by confirming the "Changes to be
   committed:" section is empty. If not empty, HALT and ask for user
   guidance.

3. Run `git status` again to see all unstaged changes.

4. Carefully review which files are relevant to the current task.

5. Stage only the relevant files using `git add <file1> <file2> ...`.
   If there is a change to a `tasks.md` marking the relevant sub-task
   as completed, include it.

6. Run `git status` again to confirm only intended files are staged.