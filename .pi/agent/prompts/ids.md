---
description: "Stop referring to entities by bare ID; include a human-readable title"
---

You referred to one or more entities — beads issues, GitHub issues, pull
requests, commits, tickets, files, jobs, etc. — by bare identifier alone.
Bare IDs are opaque to humans: `ai-config-a1b2c3` or `#4271` conveys nothing
without a lookup.

Restate what you just said, giving every entity reference a short
human-readable label alongside its ID. Look up the title if you don't already
have it. Examples of the required form:

- `ai-config-a1b2c3 (prefix parallel subagent labels with the bead ID)`
- `PR #4271 (fix race in worktree cleanup)`
- `fea0177 (feat(beads): prefix parallel subagent labels with the bead ID)`

Keep the label short — a title or a few-word summary, not a paragraph. The ID
stays, because it is what commands take as arguments; the label is what makes
the sentence legible.

**This applies for the rest of this conversation, not just to the message you
are correcting.** Every subsequent mention of an entity — in prose, in lists,
in summaries, in handoffs — must carry its label. The first mention in a
message always needs one; repeated mentions in the same immediate context may
use the bare ID once the label is established.

**Do not treat this invocation as a signal to record a new memory or amend
existing guidance.** Most likely the guidance already exists and the failure
was not following it. Adding more instructions on top of instructions you
already had does not fix that. Just fix the output and keep it fixed.
