---
description: Run linters according to repository guidelines
allowed-tools: Bash(*lint*), Bash(npm run lint), Bash(ruff), Bash(pylint), Bash(flake8), Bash(shellcheck), Bash(make lint)
---
# Running Linters

Run all appropriate linters according to the provided guidelines for
this repository (typically in `.ai-rules`, `AGENTS.md`, `AGENT.md`,
`CLAUDE.md`, `GEMINI.md`, or similar).

## Linter Discovery

Look for linting commands in:

- Repository documentation (README, AGENTS.md, etc.)
- Package configuration (package.json, Makefile, etc.)
- Standard linter patterns

If no linting guidelines are found or they are unclear, ask the user
for clarification.

## Process

For each linter found:

1. Run it.

2. If any issues are found which can be fixed either by running the
   linter in auto-fix mode (e.g. `prettier`, `eslint`, and `rubocop`
   all have auto-fix modes), then attempt to fix it.

3. If issues can't be fixed, stop and ask the user what to do next.
