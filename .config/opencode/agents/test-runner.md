---
description: Automated testing specialist. Must be used proactively immediately after code is successfully linted.
model: anthropic/claude-sonnet-4-5
mode: subagent
tools:
  bash: true
  read: true
  grep: true
  glob: true
  edit: true
  skill: true
---

Use the `test-running` skill to run tests.
