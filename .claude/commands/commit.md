---
description: Create well-formatted commits using the conventional commits style
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*), Bash(git log:*)
---
# Creating a git commit

## Goal

Create well-formatted commits with the conventional commits style.

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -40`

## Process

1. Check which files are staged with `git status`.

2. Check historical commits to learn style and tone (`git log --oneline -40`).

3. Analyze the diff to determine if multiple distinct logical changes
   are present.

4. If multiple distinct changes are detected, stop and ask the user whether to
   break the commit into multiple smaller commits.

5. Use the output of `git diff` to understand what actual changes are being
   committed

6. Commit to git using a descriptive commit message that:

   - Uses conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
     following existing style and tone

   - Roughly follows this template (wrap the body at 78 columns):

         ```txt
         feat: <what changed, keep under 75 characters>

         Without this patch, ... <describe the status quo relevant
         to this change>

         This is a problem because ... <describe *why* the change
         is needed>

         This patch solves the problem by ... <describe *how* the
         solution works>
         ```

   - Lists key changes and additions

   - References the task number and the task file it came from.

   - Adds a "Co-authored-by:" footer which clarifies which AI agent
     helped create this commit, using an appropriate `noreply@...`
     email address.

## Commit Style

- **Atomic commits**: Each commit should contain related changes that
  serve a single purpose.

- **Split large changes**: If changes touch multiple concerns, split
  them into separate commits. Always reviews the commit diff to ensure
  the message matches the changes.

- **Concise first line**: Keep the first line under 72 characters. Do
  not end the subject line with a period.

- **Present tense, imperative mood**: Use the imperative mood in the
  subject line.
