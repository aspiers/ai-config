---
description: Run tests according to repository guidelines
allowed-tools: Bash(./bin/test-*), Bash(*test*), Bash(npm test), Bash(pytest), Bash(make test)
---
# Running Tests

Run all appropriate tests according to the provided guidelines for
this repository (typically in `.ai-rules`, `AGENTS.md`, `AGENT.md`,
`CLAUDE.md`, `GEMINI.md`, or similar).

## Test Discovery

Run tests according to repository guidelines. Look for test commands in:

- Repository documentation (`README`, `CLAUDE.md`, `AGENTS.md`, etc.)
- Package configuration (`package.json`, `Makefile`, etc.)
- Standard test patterns

If no test guidelines are found or they are unclear, ask the user for
clarification.

## Process

**CRITICAL REQUIREMENT: 100% test success is MANDATORY. Less than 100% test
success is NEVER acceptable without explicit permission.**

For each test command found:

1. Run it.

2. If ANY test failures occur, they MUST be fixed. No exceptions.

3. If issues can't be fixed immediately, stop and ask the user what to do next.

4. Only consider the task complete when ALL tests pass with 100% success rate
   OR the user explicitly gives permission to ignore certain failures or
   warnings.

**NOTE:** "issues" above includes not only test failures, but also noise in
the test output such as warnings which could mask true failures.
