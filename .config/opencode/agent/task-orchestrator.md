---
description: Orchestrates the complete development workflow for implementing sub-tasks from a task list
mode: primary
tools:
  read: true
  grep: true
  glob: true
  bash: true
  edit: true
  write: true
  skill: true
permission:
  bash:
    "*": "ask"
    "ls *": "allow"
    "cat *": "allow"
    "head *": "allow"
    "tail *": "allow"
---

Use the `task-orchestration` skill to orchestrate the development workflow.
