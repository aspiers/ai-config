---
description: Create a new bead for the described issue
---

Create a new bead issue using `bd create` based on the user's description.

1. Parse the user's input to determine an appropriate short title and description.
2. Infer the issue type (`bug`, `feature`, `task`) from context; default to `task`.
3. Run: `bd create --title="<title>" --description="<description>" --type=<type> --json`
4. Report the created issue ID back to the user.
