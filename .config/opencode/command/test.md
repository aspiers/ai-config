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

For each test command found:

1. Run it.

2. If any issues are found which can be fixed, attempt to fix them.

3. If issues can't be fixed, stop and ask the user what to do next.