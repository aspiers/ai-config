# OpenCode sessions stop being discovered after `opencode-local.db` appears

## Summary

The `opencode` provider reads `~/.local/share/opencode/opencode.db`. On this
machine that database stopped receiving sessions on 2026-03-08, and a second
database, `opencode-local.db`, has been receiving them since. agentsview has no
reference to the second file, so every OpenCode session after that date is
missing with no error or warning.

I have not been able to confirm from upstream what `opencode-local.db` is, so
this report states what is observable locally and asks rather than asserts.

## Environment

- agentsview v0.40.1
- Linux
- OpenCode data directory `~/.local/share/opencode/`

## What the two databases look like

| | `opencode.db` | `opencode-local.db` |
| --- | --- | --- |
| Sessions | 576 | 111 |
| Newest session | 2026-03-08 | 2026-04-22 |
| File mtime | 2026-03-09 | 2026-04-24 |
| Tables | 10 | 14 |

They are not duplicates of each other:

- **Session IDs are near-disjoint** — only 2 of the 111 sessions in
  `opencode-local.db` also appear in `opencode.db`.
- **The schema differs.** `opencode-local.db` has the same tables plus
  `account`, `account_state`, `event`, and `event_sequence`.
- **The rows are real work**, with titles like "Create high-level summary of
  …" and "Commit staged doc update …", not placeholders or empty shells.

## Effect on agentsview

```
sqlite> SELECT MAX(started_at) FROM sessions WHERE agent='opencode';
2026-03-08T18:22:27.847Z
```

That ceiling is exactly where `opencode.db` ends. The 111 sessions in
`opencode-local.db` — including all 30 from April — are absent from the
archive.

`agentsview doctor sync` reports the root as `(ok, ...)`, because
`~/.local/share/opencode/` genuinely exists and `opencode.db` is genuinely
there. Nothing signals that a second store is being skipped.

## What I could not establish

I would rather ask than guess at the following, since a wrong assumption here
changes what the right fix is:

1. **What is `opencode-local.db`?** No OpenCode release note names it, and a
   GitHub code search for `opencode-local` across the OpenCode repository
   returns no results.
2. **Which store is authoritative now** — is `opencode.db` retired, are both
   live, or does the split depend on account or workspace state?
3. **Should both be read, or only the newer one?** If both, sessions present
   in both need de-duplicating; the 2 shared IDs here suggest overlap is
   possible.

Circumstantially, OpenCode v1.2.25 and v1.2.26 (2026-03-12 and 2026-03-13)
added "multi-account workspace authentication", "console account subcommands",
branded `WorkspaceID` through the Drizzle and Zod schemas, and "Allow passing
workspaceID into session create endpoint". That is consistent with the new
`account`, `account_state`, and `workspace` tables and with the early-March
cutover, but it is a correlation of dates and schema shape rather than
anything upstream has stated.

Note also that OpenCode's canonical repository appears to have moved from
`sst/opencode` to `anomalyco/opencode`, which may be worth reflecting in the
provider's documentation independently of this issue.

## Related

An earlier OpenCode storage change is handled correctly and is **not** what
this report is about: v1.2.0 (2026-02-14) migrated flat JSON files to a single
SQLite database, and agentsview reads that result. The legacy
`~/.local/share/opencode/storage/` tree is still present here — 92,822 JSON
files spanning 2025-09 to 2026-02 — alongside a `migration` marker file. The
gap in this report is a later, separate change.

For whatever it is worth, [`ctx`](https://github.com/ctxrs/ctx), an unrelated
session-search tool, has the same gap: at `8c6d670` (2026-08-25) it documents
`~/.local/share/opencode/opencode.db` as its source and the string
`opencode-local` appears nowhere in its repository. That suggests the second
database is simply undocumented rather than either project having missed
something obvious.

I can supply schema dumps, row counts, or a redacted sample from either
database if that would help.
