---
description: Run linters according to repository guidelines
allowed-tools: Bash(npm run lint:*), Bash(yarn run lint:*), Bash(pnpm run lint:*), Bash(npm run format:*), Bash(yarn run format:*), Bash(pnpm run format:*), Bash(ruff), Bash(pylint), Bash(flake8), Bash(shellcheck), Bash(make lint)
---
# Running Linters

Run all appropriate linters according to the provided guidelines for
this repository.

## Linter Discovery

First look for linting commands in the following order:

- Directives to AI agents (`CLAUDE.md`, `.cursorrules`, `.ai-rules`,
  `AGENTS.md`, `AGENT.md`, `GEMINI.md`, and similar)
- Repository documentation (`README.md`, `docs/`, etc.)
- Package configuration (`package.json`, `Makefile`, etc.)
- Standard linter patterns

If no linting guidelines are found or they are unclear, ask the user
for clarification.

## Process

For each linter found:

1. If it has an auto-fix mode (e.g. `prettier`, `eslint`, and `rubocop`
   all have auto-fix modes), then run that.

2. Run the linter in check mode to see if there are any remaining issues.

3. If issues can't be fixed, stop and ask the user what to do next.
