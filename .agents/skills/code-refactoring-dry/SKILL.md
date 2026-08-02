---
name: code-refactoring-dry
description: Evaluate repeated code and consolidate duplication when a shared abstraction improves correctness or maintenance. Use after introducing similar logic or when repeated changes reveal a missing source of truth.
---

# Refactoring Duplication

Remove harmful duplication without replacing clear local code with a forced
abstraction.

## Workflow

1. Compare the repeated code and the reasons each copy exists.
2. Decide whether the copies represent one concept that should change together
   or merely look similar today.
3. If one concept exists, choose the smallest natural shared boundary in the
   repository: a function, data structure, type, module, or generated source.
4. Refactor all relevant call sites while preserving behavior and useful local
   differences.
5. Run focused tests and repository quality gates appropriate to the change.

Prefer an abstraction when it creates a real source of truth, prevents drift,
or makes future changes safer. Keep duplication when sharing would couple
independent concepts, obscure control flow, or add more indirection than value.

Do not broaden a focused request into a repository-wide deduplication project.
Report nearby opportunities separately unless they are necessary for a sound
refactor.
