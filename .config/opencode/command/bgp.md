---
description: Grind through beads in parallel, each in an isolated wt worktree
---

Use the `beads-parallel-grinding` skill to work the ready beads queue,
implementing several issues concurrently in isolated git worktrees managed
by worktrunk (`wt`), so the repository's worktree lifecycle hooks are
honoured, then merging each finished branch back one at a time. Apply the
`beads-best-practices` skill throughout, including its human-attention queue
protocol.

Arguments: $ARGUMENTS

They may name a maximum number of parallel jobs, a scope restriction, both,
or neither. If no maximum is given, ask for one before starting any work.
