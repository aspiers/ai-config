---
description: Generate tasks from a PRP
argument-hint: [feature_name]
allowed-tools:
---
# Generating a Task List from a PRP

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in
Markdown format based on an existing Product Requirements Prompt (PRP). The
task list should guide a developer through implementation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `.ai/[feature-name]/tasks.md` in the repository root

## Process

1.  **Receive PRP Reference:** The user points the AI to a specific PRP file
2.  **Analyze PRP:** The AI reads and analyzes the functional requirements,
    user stories, and other sections of the specified PRP.
3.  If there are still any open questions then ask the user for clarification
    on those and amend the PRP accordingly before proceeding.
4.  **Phase 1: Generate Parent Tasks:** Based on the PRP analysis, create
    the file and generate the main, high-level tasks required to implement
    the feature. Use your judgement on how many high-level tasks to use.
    It's likely to be between 3 and 8. Present these tasks to the user in the
    specified format (without sub-tasks yet). Inform the user: "I have
    generated the high-level tasks based on the PRP. Ready to generate the
    sub-tasks? Respond with 'go' to proceed."
5.  **Wait for Confirmation:** Pause and wait for the user to respond with
    "go".
6.  **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down
    each parent task into smaller, actionable sub-tasks necessary to
    complete the parent task. Ensure sub-tasks logically follow from the
    parent task and cover the implementation details implied by the PRP.
7.  **Identify Relevant Files:** Based on the tasks and PRP, identify
    potential files that will need to be created or modified. List these
    under the `Relevant Files` section, including corresponding test files
    if applicable.
8.  **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant
    files, and notes into the final Markdown structure.
9.  **Save Task List:** Save the generated document in the location given
    above, i.e. in the same directory as the input PRP file.
10. **Commit Task List:** Ensure no other files are staged, then add the
    new task list to git, and commit with a message following this template:

    ```txt
    feat: add .ai/[feature-name]/tasks.md

    Generate tasks according to .ai/[feature-name]/prp.md
    ```

## Output Format

The generated `tasks.md` file _must_ follow this structure:

```markdown
# Context

See [prp.md][./prp.md] for the corresponding Product Requirements Prompt.

# Relevant Files

- `path/to/potential/file1.ts` - Brief description of why this file is
  relevant (e.g., Contains the main component for this feature).
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - Brief description (e.g., API route
  handler for data submission).
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Brief description (e.g., Utility functions
  needed for calculations).
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

# Tasks

- [ ] 1. Parent Task Title
  - [ ] 1.1. [Sub-task description 1.1]
  - [ ] 1.2. [Sub-task description 1.2]

- [ ] 2. Parent Task Title
  - [ ] 2.1. [Sub-task description 2.1]

- [ ] 3. Parent Task Title (may not require sub-tasks if purely structural
  or configuration)
```

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get
user confirmation ("Go") before proceeding to generate the detailed
sub-tasks. This ensures the high-level plan aligns with user expectations
before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who
will implement the feature.