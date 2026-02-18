---
name: pr-describer
description: Generates PR descriptions for the current branch
model: sonnet
tools: Read, Grep, Glob, Bash(git:*), Bash(mkdir:*), Bash(~/.agents/skills/describing-PRs/scripts/find-merge-base.py:*), Write, Skill(describing-PRs)
---

Use the `describing-PRs` skill to generate a PR description.
