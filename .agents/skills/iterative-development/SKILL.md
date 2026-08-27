---
name: iterative-development
description: >-
  Implements sub-tasks from a task list at .ai/[feature]/tasks.md strictly one
  at a time, stopping after each to ask the user before starting the next, and
  keeping the task list and Relevant Files section current. Use when the user
  wants to review or approve each sub-task before work continues, rather than
  letting the agent run the list unattended with task-orchestration.
---

# Iterative Development

Implement sub-tasks one at a time with user approval between each.

## When to Use This Skill

Use this skill when:
- Working through a task list (`.ai/[feature]/tasks.md`)
- You want user feedback between each sub-task
- Following a collaborative development workflow

## Instructions

### Sub-task Implementation

- Update the task list as you work
- Add new tasks as they emerge
- Also update the corresponding `prp.txt` as appropriate
- Maintain the "Relevant Files" section:
  - List every file created or modified
  - Give each file a one-line description of its purpose

### Sub-task Iteration (IMPORTANT)

**ONLY DO ONE SUB-TASK AT A TIME:**

- Only ever include one sub-task on your internal TODO list
  - **This is VERY IMPORTANT!**
- Do NOT start or even consider the next sub-task until you
  ask the user for permission and they say "yes" or "y"

Stop after each sub-task and wait for the user's go-ahead for the next one.

## Quality Controls

After completing each sub-task:

1. Run linters according to repository guidelines
2. Run tests according to repository guidelines
3. If linting or testing fails, fix the issues before proceeding
4. Ask for user approval before moving to the next sub-task

## Communication

After each sub-task:
1. Summarize what was accomplished
2. Report any issues encountered
3. Ask for permission to continue with the next sub-task

## Workflow

```
1. Select one sub-task from tasks.md
2. Implement it completely
3. Run linters and tests
4. Report completion
5. Ask: "Ready for the next sub-task?"
6. Wait for "yes" or "y"
7. Repeat until all sub-tasks complete
```

**Follow the above steps EXACTLY!!! NO EXCEPTIONS!!!**
