---
description: "Grind through beads in parallel, each in an isolated git worktree"
argument-hint: "<max parallel jobs> <optional scope - label / epic ID / priority / type>"
---

Use the `beads-parallel-grinding` skill to work the ready beads queue,
implementing several issues concurrently in isolated git worktrees and
merging each finished branch back into the current worktree.

Arguments: $ARGUMENTS

They may name a maximum number of parallel jobs, a scope restriction, both,
or neither. If no maximum is given, ask for one before starting any work.
