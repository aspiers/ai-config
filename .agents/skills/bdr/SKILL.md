---
name: bdr
description: >-
  Stores a persistent memory or learning with `bd remember` so it survives
  across sessions. Use when the user invokes `/bdr` or `$bdr`, or asks to
  remember, note, or persist an insight in a Beads workspace.
---

# Store a memory via Beads

Store the user's text verbatim, as a single argument:

```
bd remember "<text>"
```

Report the result back to the user.

If you were previously in the middle of working on something which this
request interrupted, resume that immediately without asking.
