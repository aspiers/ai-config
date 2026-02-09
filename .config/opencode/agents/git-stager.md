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
    "git diff *": "allow"
    "git status*": "allow"
---

Use the `git-staging` skill to stage relevant changes.
