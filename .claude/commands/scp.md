---
description: Stage relevant changes, commit them, and push
allowed-tools: Task(git-stager), Task(git-committer), Bash(git push:*)
---

The current branch's push target is: !`git rev-parse --abbrev-ref --symbolic-full-name @{push}`

First, use the `git-stager` subagent to stage relevant changes.
Then, use the `git-committer` subagent to create a well-formatted commit.
Finally, push using the remote from the upstream above:
`git push <remote> HEAD`
