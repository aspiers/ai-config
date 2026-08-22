---
description: "Grind through beads in priority order non-stop, unattended"
argument-hint: "<optional scope - label / epic ID / priority / type>"
---

I'm going to sleep now.  While I'm sleeping, make as much progress as you can
via the /bg command without asking me anything, because I won't be here to
give you an answer, and you will just get stuck and waste the opportunity to
make progress.  Commit to git as you go.  If you are unsure about something,
just use your best judgement to make a decision about how to move forward.  If
you get it wrong, it is not a disaster because we have git history so we can
always revert or rewind later.  The worst outcome would be that you just stop
and waste time, because we learn nothing that way.

Apply the `beads-best-practices` skill and `/bg` human-attention protocol. Best
judgement does not replace a criterion that genuinely requires my observation,
access, hardware, credentials, or decision. Record a checklist with
`bd comments add`, label the waiting bead `human`, run
`bd update <id> --status=open`, and verify it with
`bd human list --json`, and continue with other agent-ready work instead of
stopping.

Before the wake-up report, run `bd human list` again and put its outstanding
checklists first. Distinguish an empty agent-ready queue from work still waiting
for me.

When I wake up, I expect to see a concise report of everything you have
achieved, with any supporting information required in order to quickly test
out the things you have done.
