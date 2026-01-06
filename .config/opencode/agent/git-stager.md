---
description: Stage relevant changes via git add, taking great care not to add unrelated files or changes
mode: subagent
tools:
  read: true
  grep: true
  bash: true
  edit: true
  write: true
  skill: true
permission:
  bash:
    "*": "ask"
    "git add *": "allow"
    "git apply *": "allow"
    "git status": "allow"
    "git diff *": "allow"
    "git log *": "allow"
    "git branch": "allow"
---

# Staging Changes

Stage relevant changes via `git add`, taking great care not to add
unrelated files or changes.

## ⚠️ CRITICAL: Check for staged changes FIRST

Before any git operations, verify nothing is staged. If staged changes
exist, STOP and ask for permission.

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
