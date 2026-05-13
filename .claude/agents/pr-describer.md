---
name: pr-describer
description: Generates PR descriptions for the current branch
model: sonnet
tools: Read, Grep, Glob, Bash(git:*), Bash(mkdir:*), Bash(~/.agents/skills/describing-prs/scripts/find-merge-base.py:*), Write, Skill(describing-prs)
---

Use the `describing-prs` skill to generate a PR description.
