---
description: execute task steps of a given task list
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---
# Task List Management

Guidelines for managing task lists in markdown files to track progress on
completing a PRP.

## Task list location

`/.ai/$ARGUMENTS/tasks.md`

## Task Implementation

- **One sub-task at a time:** Do **NOT** start the next sub‑task until you
  ask the user for permission and they say "yes" or "y".

- **Completion protocol:**

  When you finish a sub‑task:

    - **Clean up**: Remove any temporary files and temporary code if
      necessary.

    - **Test / lint**: Run all appropriate tests, linters
      etc. according to the provided guidelines for this repository
      (typically in `.ai-rules` or `AGENTS.md` or `AGENT.md` or
      `CLAUDE.md` or `GEMINI.md` or similar).  If these guidelines are
      missing or unclear then stop and ask for them.

    - If any the above checks fail, try to fix them.  Do **not**
      proceed further until they all pass.

    - Mark the sub-task as completed by changing it `[ ]` to `[x]`.

    - Stage relevant changes via `git add`, taking great care not to
      add unrelated files or changes.  *Do* include the change to the
      `tasks.md` marking the relevant sub-task as completed.

    - By *default*, ask the user to review the changes and approve by
      responding either "good" or "vibe", and do *not* proceed to the
      next step until you receive one of these responses.  However, if
      the user responds "vibe", then that counts as approval not just
      this time, but also for any future time in this session - in that
      case, skip this step in the future.

    - Commit to git by following the process in
      `~/.claude/commands/commit.txt`.

  3. Once all the subtasks are marked completed and changes have been
     committed, mark the **parent task** as completed.

- Stop after each sub‑task and wait for the user's go‑ahead.

## Task List Maintenance

1. **Update the task list as you work:**

   - Mark tasks and subtasks as completed (`[x]`) per the protocol
     above.
   - Add new tasks as they emerge.
   - Also update the corresponding `prp.txt` as appropriate, although
     this should happen less frequently.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.
