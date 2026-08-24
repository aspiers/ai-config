---
description: "Review every bead blocking on human input, one by one, via the questionnaire UI"
---

Use the `beads-blocker-review` skill to work through every bead waiting on
human input, one at a time.

Ask each question with the `ask_user` interactive questionnaire tool rather
than plain text, and record the answer with `bd human respond` before moving
to the next bead. This is triage: record decisions, do not implement what they
imply.
