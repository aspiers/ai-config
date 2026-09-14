---
description: "Stage relevant changes, commit them, and push"
---

First, use the `git-staging` skill to stage relevant changes.
Then, use the `git-commit` skill to create a well-formatted commit.
Finally, resolve the current branch's push target with
`git rev-parse --abbrev-ref --symbolic-full-name @{push}`, then push to that
remote with `git push <remote> HEAD`.
