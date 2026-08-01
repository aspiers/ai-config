---
name: beads-best-practices
description: >-
  Applies reusable Beads writing and update practices in every context. Use
  whenever reading, creating, updating, commenting on, closing, superseding,
  or handing off Beads issues, including alongside beads, beads-solo, and
  plan-to-beads workflows.
---

# Beads Best Practices

Apply these practices to every Beads interaction, regardless of repository,
storage mode, team policy, or higher-level workflow.

When the repository opts into the solo-maintainer policy, also load and follow
[`beads-solo`](../beads-solo/SKILL.md). That skill controls authorization,
setup, storage, and governance; this skill controls reusable issue-writing and
update practices. Neither supersedes the other.

## Write Human-facing Content as Markdown

Treat every human-facing text field as Markdown:

- descriptions and bodies
- design and acceptance criteria
- notes, when their use is appropriate
- comments
- close or supersede reasons
- handoff and blocker updates

Use headings, paragraphs, lists, checkboxes, inline code, fenced code blocks,
and links where they make the content easier to scan.

Avoid walls of text. Separate sections and paragraphs with blank lines, and
turn sequences or sets of facts into lists. Do not rely on renderer word wrap
or single newlines inside one paragraph to provide structure.

Keep titles concise plain text; put detail in the Markdown body.

## Preserve Real Line Breaks

Pass actual newline characters to `bd`. Do not store literal `\n` sequences,
and do not compress structured content into a long one-line flag value.

Prefer stdin or file flags when the command supports them:

```bash
bd create --title="Handle expired sessions" --type=task --body-file - <<'EOF'
## Context

Expired sessions currently produce an unclear error.

## Acceptance Criteria

- Return an actionable message.
- Cover the expired-session path with a test.
EOF
```

```bash
bd update "$id" --body-file - <<'EOF'
## Context

The failure occurs before token refresh.

## Next Step

Add coverage around the refresh boundary.
EOF
```

For a multiline comment, preserve the Markdown in a shell variable or file:

```bash
comment=$(cat <<'EOF'
## Progress

- Added the regression test.
- Confirmed that it fails before the fix.

## Next Step

Update the refresh path.
EOF
)
bd comments add "$id" "$comment"
```

Use the same pattern for fields that only accept string flags. Quote every
multiline variable expansion.

## Use Comments for Chronological Updates

Append a comment rather than updating `notes` whenever time, author, order, or
history is relevant. Comments are the durable activity log and preserve the
metadata needed to understand how work evolved.

Use comments for:

- progress and handoff updates
- discoveries and investigation results
- decisions and their rationale
- blockers and unblock events
- test or review results
- changes in approach or scope

Do not append a running journal to `notes`. The notes field is not timestamped.
Reserve it, if used at all, for timeless supplementary information representing
the issue's current state and safe to replace as a whole. When in doubt, post
a comment.

## Keep Updates Useful

- State what changed, why it matters, and what happens next.
- Reference relevant issue IDs, commits, files, commands, or URLs.
- Use concrete outcomes instead of vague status such as "made progress."
- Keep each update focused; use multiple paragraphs or sections when it covers
  distinct facts.
- Never include credentials, private data, or unrelated environment details.
