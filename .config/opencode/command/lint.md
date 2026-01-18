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

Use the `code-linting` skill to run linters.
