# OpenCode sessions are invisible unless the install channel is `latest`, `beta`, or `prod`

## Summary

The `opencode` provider reads only `~/.local/share/opencode/opencode.db`.
OpenCode names its database after the **installation channel**, so anyone not
running a released build writes to `opencode-<channel>.db` instead — for a
build from source, `opencode-local.db`. agentsview never opens those files, so
every session is missing with no error or warning.

This is not a store migration and not an undocumented format. The naming rule
is explicit in OpenCode's source.

## The rule, from OpenCode's source

`packages/core/src/database/database.ts`:

```ts
export function path() {
  if (Flag.OPENCODE_DB) {
    if (Flag.OPENCODE_DB === ":memory:" || isAbsolute(Flag.OPENCODE_DB)) return Flag.OPENCODE_DB
    return join(Global.Path.data, Flag.OPENCODE_DB)
  }
  if (
    ["latest", "beta", "prod"].includes(InstallationChannel) ||
    process.env.OPENCODE_DISABLE_CHANNEL_DB === "1" ||
    process.env.OPENCODE_DISABLE_CHANNEL_DB === "true"
  )
    return join(Global.Path.data, "opencode.db")
  return join(Global.Path.data, `opencode-${InstallationChannel.replace(/[^a-zA-Z0-9._-]/g, "-")}.db`)
}
```

`packages/core/src/installation/version.ts`:

```ts
export const InstallationChannel = typeof OPENCODE_CHANNEL === "string" ? OPENCODE_CHANNEL : "local"
```

`OPENCODE_CHANNEL` is injected at build time by the release pipeline, so a
build from source leaves it undefined and the channel falls back to `"local"`.

So the set of possible database filenames is:

- `opencode.db` — channels `latest`, `beta`, `prod`, or `OPENCODE_DISABLE_CHANNEL_DB=1`
- `opencode-local.db` — any build from source
- `opencode-<channel>.db` — any other channel, sanitised to `[a-zA-Z0-9._-]`
- an arbitrary path or filename — when `OPENCODE_DB` is set

agentsview currently handles only the first.

## Effect

On this machine, after switching to a source build:

| | `opencode.db` | `opencode-local.db` |
| --- | --- | --- |
| Sessions | 576 | 111 |
| Newest session | 2026-03-08 | 2026-04-22 |
| Tables | 10 | 14 |

```
sqlite> SELECT MAX(started_at) FROM sessions WHERE agent='opencode';
2026-03-08T18:22:27.847Z
```

That ceiling is exactly where `opencode.db` stopped being written. The 111
sessions since — real work, with ordinary titles — are absent from the
archive. Session IDs are near-disjoint (2 of 111 shared), and the newer
database carries additional tables (`account`, `account_state`, `event`,
`event_sequence`), so the two cannot be treated as copies of one another.

`agentsview doctor sync` reports the root as `(ok, ...)`, because the
directory and `opencode.db` both genuinely exist. Nothing signals that a live
database beside them is being skipped.

## Suggested handling

The discovery rule is mechanical, so it can mirror the upstream logic:

- Glob `opencode*.db` in the data directory rather than hard-coding one name.
- Treat each matching database as a source in its own right. A user who has
  switched channels will legitimately have several, each holding a distinct
  slice of history, and dropping the older ones loses sessions.
- De-duplicate by session ID where databases overlap, since a channel switch
  can copy or share some rows.
- Optionally honour `OPENCODE_DB`, which can point anywhere, including outside
  the data directory.

A narrower fix — adding `opencode-local.db` alone — would cover builds from
source but still miss `opencode-beta.db` and any custom channel.

## Workaround

Setting `OPENCODE_DISABLE_CHANNEL_DB=1` makes a non-release build write to
`opencode.db`, which agentsview already reads. That is useful to know, but it
requires knowing the mechanism exists, and it does not recover sessions
already written to a channel database.

## Environment

- agentsview v0.40.1
- Linux
- OpenCode data directory `~/.local/share/opencode/`

## Related

An earlier OpenCode storage change is handled correctly and is **not** what
this report is about: v1.2.0 (2026-02-14) migrated flat JSON files to a single
SQLite database, and agentsview reads that result.

[`ctx`](https://github.com/ctxrs/ctx), an unrelated session-search tool, has
the same gap: at `8c6d670` (2026-08-25) it documents
`~/.local/share/opencode/opencode.db` as its source and the string
`opencode-local` appears nowhere in its repository.

Note also that OpenCode's canonical repository appears to have moved from
`sst/opencode` to `anomalyco/opencode`, which may be worth reflecting in the
provider's documentation independently of this issue.

I am happy to supply schema dumps or row counts from either database, and to
test a fix against a machine that has both.
