---
description: Commits staged changes to git with proper conventional commit messages
mode: subagent
tools:
  read: true
  grep: true
  glob: true
  bash: true
  edit: false
  write: false
  skill: true
permission:
  bash:
    "*": "ask"
    "git commit *": "allow"
    "git status": "allow"
    "git log *": "allow"
    "git diff *": "allow"
    "git show *": "allow"
    "git branch": "allow"
---

Use the `git-commit` skill to create commits.
