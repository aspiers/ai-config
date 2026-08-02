---
name: code-refactoring-small
description: Refactor code units whose size or mixed responsibilities impede understanding, testing, or change. Use when recent work makes a function, class, or module materially harder to reason about.
---

# Refactoring Large Code Units

Improve cohesion and readability rather than optimizing for an arbitrary line
count.

## Workflow

1. Read the whole unit and its important callers or tests.
2. Identify the concrete source of difficulty: mixed responsibilities, deep
   nesting, hidden state transitions, repeated setup, or an unstable boundary.
3. Choose extractions that have meaningful names and inputs. Follow existing
   repository structure rather than introducing layers solely to make units
   shorter.
4. Preserve behavior and public contracts unless the task explicitly changes
   them.
5. Verify with focused tests and the repository's normal quality gates.

A long linear function may be clearer than many tiny helpers; a short function
may still combine unrelated responsibilities. Use size as a prompt to inspect,
not a pass/fail threshold.

Keep the refactor scoped to what improves the current change. If a larger
architectural split is justified, explain the trade-off and seek agreement
before expanding scope.
