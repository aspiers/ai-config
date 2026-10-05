@../.agents/AGENTS.md

## Text before a tool call

On recent Claude models, prose written immediately before a tool call can
reach the user only as a one-line summary, or not at all, while your own
context keeps the full text. This includes text written just before an
`AskUserQuestion` call.

- Never assume the user saw anything you wrote mid-turn, and never point
  a question or a later message at it as "above".
- Put drafts, tables and other material the user must review before
  answering in a file under `tmp/`, and name its path in the question.
- If told that content was not shown to the user, write it out in full as
  your reply.
