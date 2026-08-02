---
name: code-reviewing
description: Review changed code for correctness, security, maintainability, and verification gaps. Use when code is ready for independent review or before handoff, staging, or merge.
---

# Code Review

Review the change in its repository context and report actionable findings,
not a generic style checklist.

## Establish scope

Inspect the request, applicable project guidance, working-tree state, staged
and unstaged diffs, and relevant surrounding code. Use history when it helps
explain local conventions or intent.

If the review target is ambiguous, state the assumed range or ask one focused
question. Do not mix unrelated pre-existing code into the findings without
labelling it.

## Review priorities

Use judgement based on the change's risk. Consider:

- correctness, edge cases, and error handling;
- security, privacy, trust boundaries, and secret exposure;
- compatibility, migrations, and public contracts;
- concurrency, state consistency, resource use, and performance;
- maintainability in the repository's existing idiom; and
- whether tests and other verification support the claimed behavior.

Duplication, function length, and naming are signals rather than universal
failures. Recommend refactoring only when it makes this code clearer or safer.

## Findings

Lead with findings ordered by severity. For each one include:

- the precise file and line or symbol;
- the behavior or risk;
- why it matters in a realistic scenario; and
- a concrete direction for resolution when useful.

Separate blocking defects from non-blocking suggestions. Avoid praise,
restating the diff, or speculative concerns without a plausible failure mode.
If no findings remain, say so and identify any important verification limits.
