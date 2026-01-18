---
description: Run tests according to repository guidelines
permission:
  bash:
    "./bin/test-*": "allow"
    "*test*": "allow"
    "npm test": "allow"
    "pytest": "allow"
    "make test": "allow"
---

Use the `test-running` skill to run tests.
