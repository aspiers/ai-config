---
description: Stage relevant changes via git add
allowed-tools: Bash(git add:*), Bash(git status:*)
---
# Staging Changes

Stage relevant changes via `git add`, taking great care not to add
unrelated files or changes.

## Guidelines

- First check whether anything is already staged, and if so, ask
  the user how to proceed before doing anything else.
- Only stage files that are directly related to the current task.
- Include the change to `tasks.md` marking the relevant sub-task as completed.
- Use `git status` to review what will be staged.
- Use selective staging (`git add <specific-files>`) rather than `git add .`

## Process

1. Run `git status` to see all changes
2. If anything is already staged, ask
   the user how to proceed before doing anything else.
3. Carefully review which files are relevant to the current task
4. Stage only the relevant files using `git add <file1> <file2> ...`
5. Run `git status` again to confirm only intended files are staged
