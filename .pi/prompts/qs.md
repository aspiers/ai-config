---
description: "Re-ask the most recent question using the interactive questionnaire UI"
---

Re-ask the most recent question you posed to the user, this time using the
`ask_user` interactive questionnaire tool instead of plain text.

**Reminder**: You should ALWAYS use the `ask_user` tool when presenting
the user with choices or multiple questions. Plain-text questions at the end of
messages are easy to miss and don't surface options clearly. This is not
optional — it is a mandatory rule from the agent instructions. Apply this not only now but
for the rest of this conversation: every future question with concrete options
must use the questionnaire tool, not plain text.
