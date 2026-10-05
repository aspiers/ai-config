@../.agents/AGENTS.md

## Text before a tool call

On recent Claude models, prose written immediately before a tool call can
reach the user only as a one-line summary, or not at all, while your own
context keeps the full text. This includes text written just before an
`AskUserQuestion` call.

- Never assume the user saw anything you wrote mid-turn, and never point
  a question or a later message at it as "above".
- Write drafts, tables and findings the user must review before answering
  a questionnaire as plain text immediately before it, never only in a
  file. A hook makes you restate that text as a reply if it was hidden.
- If told that content was not shown to the user, write it out in full as
  your reply.
