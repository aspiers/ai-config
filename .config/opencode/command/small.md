---
description: Refactor overly large code you just added or extended
---

# SMALL - Keep Code Units Small and Focused

You recently made changes to this codebase that added or extended functions, methods, classes, or files that are becoming too large. Identify and refactor these bloated code units into smaller, more focused components.

## Instructions

1. **Identify the bloat**: Review your recent changes (committed or uncommitted) to find:
   - Functions or methods that are too long (typically >50 lines)
   - Classes that have too many responsibilities
   - Files that have grown too large or handle multiple concerns
   - Deeply nested code blocks

2. **If the bloat is not obvious**: Ask the user to clarify which specific code units they want refactored before proceeding.

3. **Refactor**: Once the bloat is identified:
   - Extract logical sub-operations into separate functions/methods
   - Split large classes following Single Responsibility Principle
   - Move related functionality into separate modules/files
   - Reduce nesting levels by extracting guard clauses or helper functions
   - Ensure each unit does one thing well (UNIX Philosophy)

4. **Verify**: After refactoring:
   - Run linters and tests if available
   - Verify the code still works as expected
   - Check that the solution is clearer and more maintainable
   - Ensure the refactoring improved readability

## Goal

Break down large, complex code units into smaller, focused components that are easier to understand, test, and maintain. Each function, class, or file should have a clear, single purpose.
