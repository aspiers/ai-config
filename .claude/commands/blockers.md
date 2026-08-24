---
description: Review every bead blocking on human input, one by one, via the questionnaire UI
allowed-tools: Skill(beads-blocker-review), AskUserQuestion, Bash(.agents/skills/beads-blocker-review/scripts/list-actionable-human-beads.py:*), Bash(~/.agents/skills/beads-blocker-review/scripts/list-actionable-human-beads.py:*), Bash(*/.agents/skills/beads-blocker-review/scripts/list-actionable-human-beads.py:*), Bash(bd human:*), Bash(bd show:*), Bash(bd comments:*), Bash(bd label:*), Bash(bd gate:*), Bash(bd dep:*), Bash(bd ready:*)
---

Use the `beads-blocker-review` skill to work through every bead waiting on
human input, one at a time.

Ask each question with the `AskUserQuestion` interactive questionnaire tool
rather than plain text, and record the answer with `bd human respond` before
moving to the next bead. This is triage: record decisions, do not implement
what they imply.
