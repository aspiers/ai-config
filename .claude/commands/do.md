---
description: execute a single sub-task from a given task list
argument-hint: [feature_name [subtask_number]]
---
# Sub-task implementation

**Follow the below steps EXACTLY!!! NO EXCEPTIONS!!!**

Process for completing a sub-task from a task list whilst
adhering to strict quality controls.

## Command Arguments

- `$ARGUMENTS` are:
  1. `feature_name` - this allows location of the relevant task list
     at `.ai/[feature_name]/tasks.md`.  If it's not provided, run `ls
     .ai/*/tasks.md`, show the feature names as a numbered list, and
     ask the user to pick one to work on, excluding ones which are
     already complete.

  2. `subtask_number` - the number of the specific sub-task to
     implement.  If it's not provided, show the user all unimplemented
     sub-tasks, then say which is the first unimplemented one and ask
     if they'd like to implement that one, and if not, which other one
     to do.

## Task list location

`.ai/[feature_name]/tasks.md`

## Sub-task completion protocol (IMPORTANT)

**Follow the below steps EXACTLY!!! NO EXCEPTIONS!!!**

1. Use the task-implementer sub-agent to implement the selected
   subtask.

2. Use the code-linter sub-agent to run all appropriate linters
   according to repository guidelines.

3. Use the test-runner sub-agent to run all appropriate tests
   according to repository guidelines.

4. If any of the above checks fail, try to fix them.  Do **not**
   proceed further until both linters and tests are all passing.

5. Mark the sub-task as completed by changing it `[ ]` to `[x]`.  If
   all the subtasks under a parent task are marked completed then
   also mark the **parent task** as completed.

6. Use the git-stager sub-agent to stage relevant changes,
   taking great care not to add unrelated files or changes.  *Do*
   include the change to the `tasks.md` marking the relevant sub-task
   as completed.

7. By *default*, ask the user to review the changes and approve by
   responding either "good" or "vibe", and do *not* proceed to the
   next step until you receive one of these responses.  However, if
   the user responds "vibe", then that counts as approval not just
   this time, but also for any future time in this session - in that
   case, skip this step in the future.

8. ONLY AFTER getting a review in step 7, use the git-committer
   sub-agent to commit to git with a proper commit message.

9. Select the first incomplete sub-task from `tasks.md`, and repeat
   from step 1 until all steps are done.

**Follow the above steps EXACTLY!!! NO EXCEPTIONS!!!**
