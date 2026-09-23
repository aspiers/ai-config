---
name: xero-mcp
description: Use the Xero MCP server — troubleshoot its self-refreshing OAuth2 token file, maintain the local best-of-breed server build, and pick up other operational notes for working with Xero MCP tools. Use when Xero MCP tools fail with authentication errors, before starting any Xero workflow, when adding or updating upstream xero-mcp-server PRs, or for general guidance on Xero MCP usage.
---

# Xero MCP

Covers usage of the Xero MCP server, including authentication
(OAuth2 bearer tokens) and related operational notes.

For browser-driven automation of the Xero web UI (not via MCP), see the
separate [`xero-browser`](../xero-browser/SKILL.md) skill instead.

## MCP vs browser — which to use (READ FIRST)

**Before any Xero data task, read [`references/mcp-vs-browser.md`](references/mcp-vs-browser.md).**
It is the single source of truth for choosing MCP tools vs the browser
Account Transactions report (shared with the `xero-browser` skill — do
not duplicate its content here). Key rule: Xero MCP has **no per-account
transaction endpoint**, so a single account's full ledger comes from the
browser report, never from paginating `list-manual-journals`.

## Authentication

The server reads a self-refreshing OAuth2 token file on every tool call,
so tokens never need refreshing by hand and **the agent session never
needs restarting for auth**. Several servers (Claude Code, Pi, OpenCode)
share the file safely.

### On an auth error: diagnose — do NOT limp to workarounds

An "Authentication failed" / 401 from a Xero MCP tool is not a routine
expiry any more. Do not retry blindly, and do not switch to a browser /
block-explorer / Cryptio workaround "to keep moving": the MCP path is far
faster and more reliable. Instead, read
[`references/authentication.md`](references/authentication.md) — the
usual causes are a scope the token lacks (one tool fails, others work)
or a refresh token unused for 60 days (every tool fails), which needs the
user to run the browser OAuth flow.

The ONLY time a browser fallback is right is when the data genuinely
isn't available via MCP at all (e.g. a per-account transaction ledger —
see `references/mcp-vs-browser.md`).

**Also read [`references/authentication.md`](references/authentication.md)**
for first-time setup, after revoking and re-authorizing the Xero app, or
when changing scopes. It covers the `xero-oauth` script, `.env`
configuration, Xero app registration, the refresh-vs-full-flow choice,
and the scopes newer tools need.

## The server is a local best-of-breed build

Upstream `@xeroapi/xero-mcp-server` is effectively unmaintained, so the
configs run a local build that merges ~28 reviewed upstream PRs plus
local fixes (xero-node v20, token-file locking). Tools and behaviour
therefore differ from upstream's README. For which PRs are in, how to
rebuild after changes, and how to add a new upstream PR, see
[`references/local-server.md`](references/local-server.md).

## Searching for records

The MCP list-* tools paginate at 10 records per page by default; most
accept `pageSize` (up to 100). Absence on page 1 is **not** absence in
Xero. Before concluding a record is missing, search by ID directly or
page exhaustively.

See [`references/searching-records.md`](references/searching-records.md)
for the rules around `list-manual-journals`, `list-invoices`,
`list-bank-transactions`, and `list-contacts`.

## Manual journals (create / update / void)

The schema descriptions for `create-manual-journal` and
`update-manual-journal` are misleading on at least two points:

- `lineAmountTypes: "NO_TAX"` is rejected by the Xero API (use the
  default — omit the field — which serialises as `NoTax`).
- `update-manual-journal` says "Only works on draft manual journals",
  but in practice mutates POSTED MJs (narration, date, lines, status).

This makes the **void-and-replace** pattern (create new POSTED MJ
referencing the old UUID, then update the old to `status: VOIDED`)
viable via MCP without touching the web UI.

The response strings from the write tools also render input params
verbatim and show line items as `[object Object]` — so always confirm
state with `list-manual-journals manualJournalId=<uuid>` after every
write before trusting it.

See [`references/manual-journals.md`](references/manual-journals.md)
for the full void-and-replace recipe, common error messages, and the
token-expiry coupling that bites multi-step MJ workflows.
