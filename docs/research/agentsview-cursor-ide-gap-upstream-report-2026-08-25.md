# Cursor IDE (GUI) sessions are never discovered — transcripts live in `cursorDiskKV`, not `agent-transcripts`

## Summary

The `cursor` provider reads only `~/.cursor/projects/<project>/agent-transcripts/*.{jsonl,txt}`,
which is the **Cursor Agent CLI** store. **Cursor IDE (the GUI)** writes its
chats to the VS Code-style state database instead:

```
~/.config/Cursor/User/globalStorage/state.vscdb      # Linux
~/Library/Application Support/Cursor/User/globalStorage/state.vscdb   # macOS
```

in the `cursorDiskKV` table, keyed as:

- `composerData:<uuid>` — one session document
- `bubbleId:<uuid>:<uuid>` — one turn of that session

Nothing in the parser reads that store, so a user who works in the Cursor GUI
and never runs the CLI gets **zero Cursor sessions**, with no error or warning.
`agentsview doctor sync` reports the root as `(ok, ...)` because
`~/.cursor/projects` genuinely exists — it just holds MCP tool caches,
`terminals/` and `rules/` rather than transcripts.

## Environment

- agentsview v0.40.1
- Linux; Cursor IDE installed, `cursor-agent` CLI never run

## Evidence

On one machine, the GUI store holds a substantial history that agentsview
cannot see:

| `cursorDiskKV` key prefix | Rows | Bytes |
| --- | --- | --- |
| `composerData:` | 648 | 60 MB |
| `bubbleId:` | 38,178 | 307 MB |
| `checkpointId:` | 9,002 | 89 MB |

Of the 648 `composerData` rows, **381 are real conversations** (≥2 messages),
spanning Jan 2025 – Jan 2026; the rest are empty composers. The `bubbleId`
rows carry actual message text — 13,070 with non-empty `text`: 3,054 of
`type: 1` (user) and 10,016 of `type: 2` (assistant). `PRAGMA quick_check`
returns `ok`.

Meanwhile the configured root on the same machine contains **no transcripts at
all**: 14 project directories, of which exactly one has an `agent-transcripts`
directory, and that directory is empty. The other 13 have none. Every JSON file
under those directories is an MCP tool-schema cache.

That asymmetry is the whole bug: 381 conversations in the store agentsview does
not read, 0 in the store it does.

## Why this is not machine-specific

The split is by **product**, not by configuration:

- **Cursor Agent (CLI)** → `~/.cursor/projects/<project>/agent-transcripts/<id>/<id>.jsonl`,
  with metadata in `~/.cursor/chats/<workspace-hash>/<id>/store.db`
- **Cursor IDE (GUI)** → `globalStorage/state.vscdb`, table `cursorDiskKV`

Corroboration from outside this report:

- Another local-history tool states it *"does not claim full Cursor IDE chat
  history support because DB-only Cursor chat message blobs are not decoded as
  transcript events"* — i.e. it hits the same wall.
- An independent teardown of a machine holding **all** the stores found
  `agent-transcripts` covering ~130 sessions while `composerData`/`bubbleId`
  held 509+ MB, and concluded Cursor has "at least two replay stacks".

So any Cursor GUI user should see this. The docs note in
`docs/internal/session-format-sources.md` that `state.vscdb` is "metadata" is
accurate for the **CLI** — where the JSONL is primary — but not for the GUI,
where it is the only store.

This also looks like an ecosystem-wide blind spot rather than an agentsview
oversight. [`ctx`](https://github.com/ctxrs/ctx), an unrelated Rust
session-search tool with its own provider architecture, has the same gap: at
`8c6d670` (2026-08-25) its `ctx-history-provider-claude-cursor` crate reads
`agent-transcripts` only, and the strings `cursorDiskKV`, `composerData` and
`bubbleId` appear nowhere in the repository. Two independent implementations
both followed the CLI/documented path, which is consistent with the GUI store
simply being undocumented rather than either project having missed something
obvious.

## Suggested direction

A separate provider looks like the right shape; the existing Cursor parser
should not need to change.

- **Precedent for the split:** Kiro already ships `kiro.go` (CLI) alongside
  `kiro_ide.go` + `kiro_ide_provider.go` with a distinct agent constant. A
  `cursor-ide` agent would mirror that. (Kiro IDE is file-based, so it is a
  precedent for the split, not for SQLite reading.)
- **Precedent for the storage shape:** `multiSessionContainerSourceSet` in
  `internal/parser/multi_session_container.go` already models "one database,
  many sessions", and Omnigent uses it against a SQLite `chat.db`. With
  `sqlite_container_state.go` and `sqlite_dsn.go`, discovery, watching,
  changed-path classification, fingerprinting and incremental parse come from
  the framework; the provider supplies `discoverContainers` and
  `parseContainer`/`parseMember` closures.
- **The genuinely new work** is a decoder mapping `composerData` → session and
  `bubbleId` → messages onto `ParseResult`/`ParsedMessage`, plus session
  metadata (name, model, timestamps, and workspace/cwd from the `gitWorktree`
  block in `composerData`).

For whatever it is worth as an outside data point, `ctx` factors its
SQLite-backed agents (opencode, zed, deepagents, forgecode) into a dedicated
`ctx-history-providers-sqlite-logical` crate — the same shape as routing this
through `multiSessionContainerSourceSet` rather than extending the existing
file-based Cursor provider.

Known risks worth flagging: the blob schema is undocumented and
version-dependent — Cursor 3.16.29 shrank/wiped some users' `cursorDiskKV` on
update — so a decoder must tolerate schema drift and partial data; and at
38k+ bubble rows, whole-container fingerprinting on a constantly-mutating
database needs care to avoid repeated full re-reads.

## Prior art in this tracker

Closest match is the Qoder report (#1233), which had the same shape — sessions
not synced because the data lived somewhere other than the configured
directory — and was fixed. Existing Cursor issues cover a different area:
#504 is an `ApplyPatch` rendering bug (implying a CLI user), and #574 / #853
cover Cursor **admin usage/cost** ingestion rather than transcripts.

I searched issues, PRs and discussions for `cursorDiskKV`, `composerData`,
`bubbleId`, "Cursor IDE" and "Cursor GUI" and found no existing report of this
gap, but I may have missed one.

Happy to contribute the provider if that would be welcome — though I would
rather check first whether you would prefer to own the decoder, given the
schema-drift risk.
