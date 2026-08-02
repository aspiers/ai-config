---
name: incremental-commits
description: Plan dependency-aware atomic commits for changes that span multiple logical concerns. Use when a refactor, feature, or API change would benefit from reviewable, independently meaningful commit boundaries.
---

# Incremental Commits

Turn a multi-concern change into a reviewable sequence without forcing every
multi-file edit into multiple commits.

## Decide whether to split

Split when commits represent independently understandable concerns, improve
review or rollback, or establish dependencies needed by later work. Keep one
commit when separating the change would create misleading, broken, or
meaningless intermediate states.

File count is evidence, not a rule. Avoid both catch-all commits and
one-symbol micro-commits.

## Plan the sequence

1. Inventory the changed and expected files and identify logical concerns.
2. Map dependencies between those concerns. Foundations and contracts usually
   precede consumers, but follow the actual code rather than a fixed layer
   template.
3. Choose boundaries that are coherent and, when practical, buildable and
   testable on their own.
4. Note any unavoidable temporary incompatibility and decide whether it makes
   a split less useful.

## Implement and verify

For each planned commit:

1. Change or stage only that concern.
2. Run the smallest relevant checks required by the repository.
3. Review the staged diff as a standalone change.
4. Commit using the `git-commit` skill.
5. Reassess later boundaries if implementation reveals a better grouping.

Run the final repository quality gates after the sequence. The history should
explain the change in dependency order without requiring later commits to make
an earlier commit truthful.

## Common failure modes

- **Monolith:** unrelated behavior, cleanup, and dependency changes share one
  commit merely because they were developed together.
- **Artificial sequence:** a fixed “types, factories, API, consumers” pattern
  is imposed even though the repository has different boundaries.
- **Micro-history:** mechanical fragments cannot be reviewed or reverted
  meaningfully on their own.
- **Broken middle:** an intermediate commit fails required checks without a
  documented reason.
