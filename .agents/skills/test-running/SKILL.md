---
name: test-running
description: Discover and run tests that provide meaningful evidence for a code change. Use after implementation, before handoff or commit, or when the user asks to validate behavior.
---

# Test Running

Choose tests from the behavior and risk of the change, guided by repository
instructions and existing test interfaces.

## Workflow

1. Read applicable project guidance and test configuration.
2. Identify the smallest tests that exercise the changed behavior, plus any
   broader gate required by the repository.
3. Run targeted tests early for fast feedback; run required broader tests
   before completion when practical.
4. Diagnose failures before editing. Distinguish product regressions from
   pre-existing failures, flaky behavior, missing services, and environment
   problems.
5. Re-run affected tests after fixes and report commands, scope, and results.

Add or update coverage when the change introduces behavior that the repository
would normally test. Avoid tests that merely mirror implementation details.

## Completion evidence

A passing command is evidence only for the scope it executed. State skipped,
unavailable, flaky, or unrelated failing tests explicitly rather than
reporting an unconditional pass.

Fix failures caused by the current work. For unrelated or infeasible failures,
preserve the evidence and follow repository or user policy on whether they
block completion; do not hide them or redefine warnings as success.
