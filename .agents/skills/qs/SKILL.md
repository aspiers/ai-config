---
name: qs
description: >-
  Re-asks the most recent question through the agent's interactive
  questionnaire tool instead of plain text, and keeps using that tool for
  every later question with concrete options. Use when the user invokes `/qs`
  or `$qs`, or asks for a question to be re-posed as selectable choices.
---

# Re-ask the last question interactively

Re-ask the most recent question you posed to the user, this time using the
current agent's interactive questionnaire tool instead of plain text. In
Claude Code that tool is `AskUserQuestion`; other agents expose an equivalent
ask-the-user tool.

**Reminder**: ALWAYS use that tool when presenting the user with choices or
multiple questions. Plain-text questions at the end of messages are easy to
miss and don't surface options clearly. This is mandatory under the agent
instructions. Apply it for the rest of this conversation: every future
question with concrete options must use the questionnaire tool, not plain
text.
