# Searching for Xero records via MCP

## Identifying manual journals: UUID, not `#NNNNN`

The MCP response **does not include** Xero's user-facing sequential
journal number (e.g. `#11868`). Only the `Manual Journal ID` (a UUID
like `deadbeef-0000-4000-8000-000000000000`) is returned.

This is fine, because the sequential `#NNNNN` is **unstable**: every
edit-in-place via Journal Options → Edit causes Xero to bump it to a
new number, while the UUID stays the same. A note that says "#11799"
today may point at "#11868" tomorrow after a single edit.

**Rule:** in notes, todos, commit messages, and any other persisted
artefact, every reference to a manual journal must include either the
**full UUID** (e.g. `deadbeef-0000-4000-8000-000000000000`) or — preferably —
the full click-through URL
`https://go.xero.com/Journal/View.aspx?invoiceID=<full-uuid>`. You cannot
reconstruct the URL without the full UUID anyway, so the URL form is
strictly better. A **truncated UUID prefix** (first segment, e.g.
`ba0b0afa`) is convenient shorthand for repeated mentions of the same
journal in the same document — but only after the full UUID/URL has been
recorded somewhere nearby. Never search for a journal by `#NNNNN` —
there is no MCP filter for it anyway. The `#NNNNN` is acceptable as
transient context inside a single conversation, but treat it as
ephemeral.

## `list-manual-journals` returns 10 per page by default

The `mcp__xero__list-manual-journals` tool returns at most 10 results
per call. Absence on page 1 is **not** absence in Xero — it just means
the record isn't in the first 10 returned by Xero's sort order.

The `modifiedAfter` filter narrows by modification timestamp (not
transaction date), but the resulting set may still be larger than 10,
and the sort order is **not** simply "newest modified first" — it
appears to mix modification date with other heuristics. A journal
modified inside the window can still land on page 2+.

**Rule:** before concluding "not in Xero", do one of the following:

1. **Search by the known ID directly** with
   `list-manual-journals manualJournalId=<uuid>` — single-record lookup
   bypasses pagination entirely.
2. **Search by the source transaction hash** — journals imported
   from upstream sync tooling often embed the tx hash (e.g.
   `0xdeadbeef00000000000000000000000000000000000000000000000000000000`)
   in the journal `Description`. Page through with explicit `page`
   parameter and grep descriptions, or pull a wider window with
   `modifiedAfter` and a known earlier date.
3. **Page exhaustively** until the result count drops below 10 — only
   then is the absence conclusive.

## `list-invoices`, `list-bank-transactions`, `list-contacts`

Same caveat applies. `list-bank-transactions` has **no date filter**
at all — pagination is the only way to reach older entries, and the
default sort is by last-modified (so a 2024 entry recently re-touched
will appear before older 2025 entries). Do not infer "missing from
Xero" from a single page.

When looking for a specific imported bank transaction:

- Match by the upstream sync URL in the line description, OR
- Match by tx hash if embedded, OR
- Use `list-manual-journals` first — most synced crypto activity
  lands as manual journals, not bank transactions.

## Background

The MCP tool wraps Xero's REST API, which paginates at 100 entries
server-side but the MCP wrapper truncates to 10 per response to keep
context bounded. The MCP tool descriptions themselves prompt you to
"call this tool again with the next page number" — that's a load-
bearing instruction, not a suggestion.
