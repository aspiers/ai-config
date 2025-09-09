---
description: Run linters according to repository guidelines
permission:
  bash:
    "npm run lint": "allow"
    "yarn run lint": "allow"
    "pnpm run lint": "allow"
    "npm run format": "allow"
    "yarn run format": "allow"
    "pnpm run format": "allow"
    "ruff": "allow"
    "pylint": "allow"
    "flake8": "allow"
    "shellcheck": "allow"
    "make lint": "allow"
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

**IMPORTANT:** Do **not** ignore unfixed issues!  These are totally
unacceptable unless the user gives permission to defer their resolution until
later!
