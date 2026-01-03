---
description: Remove code duplication you just introduced
---

# DRY - Don't Repeat Yourself

You recently made changes to this codebase that introduced code duplication. Identify and refactor the duplicated code to follow the DRY principle.

## Instructions

1. **Identify the duplication**: Review your recent changes (committed or uncommitted) to find duplicated code patterns, logic, or structures.

2. **If the duplication is not obvious**: Ask the user to clarify which specific duplication they want addressed before proceeding.

3. **Refactor**: Once the duplication is identified:
   - Extract shared logic into reusable functions, classes, or modules
   - Replace duplicated code with calls to the shared implementation
   - Ensure the refactoring maintains the same functionality

4. **Verify**: After refactoring:
   - Run linters and tests if available
   - Verify the code still works as expected
   - Check that the solution is cleaner and more maintainable

## Goal

Eliminate unnecessary duplication while maintaining code clarity and functionality. The refactored code should be easier to maintain and modify in the future.
