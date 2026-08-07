---
description: Grind through beads in parallel, each in an isolated wt worktree
argument-hint: <max parallel jobs> <optional scope - label / epic ID / priority / type>
allowed-tools: Skill(beads-parallel-grinding), Task, AskUserQuestion, Bash(bd ready:*), Bash(bd show:*), Bash(bd update:*), Bash(bd close:*), Bash(bd create:*), Bash(bd dep:*), Bash(wt switch:*), Bash(wt merge:*), Bash(wt remove:*), Bash(wt list:*), Bash(wt hook show:*), Bash(wt step:*), Bash(wt --version), Bash(git status:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(ai-notify:*)
---

Use the `beads-parallel-grinding` skill to work the ready beads queue,
implementing several issues concurrently in isolated git worktrees managed
by worktrunk (`wt`), so the repository's worktree lifecycle hooks are
honoured, then merging each finished branch back one at a time.

Arguments: $ARGUMENTS

They may name a maximum number of parallel jobs, a scope restriction, both,
or neither. If no maximum is given, ask for one before starting any work.
