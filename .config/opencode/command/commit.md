---
description: Create well-formatted commits using the conventional commits style
permission:
  bash:
    "git status": "allow"
    "git commit *": "allow"
    "git diff *": "allow"
    "git log *": "allow"
    "git add *": "deny"
    "git stage *": "deny"
    "git reset *": "deny"
    "git restore *": "deny"
---

Use the `git-commit` skill to create a well-formatted commit.
