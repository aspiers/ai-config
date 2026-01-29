---
description: Generates PR descriptions for the current branch
mode: subagent
tools:
  read: true
  grep: true
  glob: true
  bash: true
  edit: false
  write: true
  skill: true
permission:
  bash:
    "*": "ask"
    "git *": "allow"
    "mkdir *": "allow"
    "~/.claude/skills/describing-PRs/scripts/find-merge-base.py *": "allow"
---

Use the `describing-PRs` skill to generate a PR description.
