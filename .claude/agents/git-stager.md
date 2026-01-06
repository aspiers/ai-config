---
name: git-stager
description: Stage relevant changes via git add, taking great care not to add unrelated files or changes
tools: Read, Edit, Write, Grep, Skill(git-staging), Bash(git add:*), Bash(git apply:*), Bash(git branch:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*)
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

3. Load the `git-staging` skill and follow its techniques for staging.
   **Do NOT use interactive commands like `git add -p`**.

4. If there is a change to a `tasks.md` marking the relevant sub-task
   as completed, include it.

5. Run `git status` to confirm only intended changes are staged.
