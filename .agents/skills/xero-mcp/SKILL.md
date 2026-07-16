---
name: xero-mcp
description: Use the Xero MCP server — obtain/refresh OAuth2 bearer tokens, troubleshoot authentication, and pick up other operational notes for working with Xero MCP tools. Use when Xero MCP tools fail with authentication errors, when the bearer token has expired (tokens last ~30 min), before starting any Xero workflow, or for general guidance on Xero MCP usage.
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

The Xero MCP server needs a valid bearer token
(`XERO_CLIENT_BEARER_TOKEN`) in its environment. Tokens last ~30 minutes
and must be refreshed via the `xero-oauth` helper script.

### On a 401: STOP, refresh, ask for restart — do NOT limp to workarounds

When any Xero MCP tool returns a **401 / auth error**, the correct
response is a fixed sequence — not retrying and not falling back:

1. **Stop.** Do NOT call the tool 2–3 more times hoping it recovers — a
   401 is an expired token, it will not self-heal. Do NOT switch to a
   browser / block-explorer / Cryptio workaround "to keep moving".
2. **Refresh the token:** run `xero-oauth --refresh` (writes the new
   token to `.mcp.json` / `opencode.json` / `.env`).
3. **Ask the user to restart Claude Code, then END YOUR TURN.** A disk
   refresh does NOT reach the *running* MCP server — it only picks up the
   new token on restart (see `reference_xero_mcp_token_restart` / the note
   below). So a long MCP workflow that 401s cannot self-heal
   mid-conversation; state that plainly and request the restart.

   **Do not do ANY other work after requesting the restart** — not even
   tasks needing no Xero access. The restart kills the process you are
   running in, so there is no "meanwhile": you cannot work *while* the
   user restarts you. Continuing either gets thrown away by the restart,
   or stalls it because the user is waiting for you to stop. The only
   permitted action between the refresh and the restart is persisting
   resume state (exact retry params) so the fresh session can pick up
   where you left off. Then stop, in the same turn.

**Why this is the rule, not a suggestion:** the MCP path is far faster
and more reliable than every workaround (browser Account Transactions
report, block-explorer queries, Cryptio cross-checks). Burning turns on
retries and then a slow browser workaround is worse on every axis than a
30-second refresh + restart. The ONLY time a browser fallback is right is
when the data genuinely isn't available via MCP at all (e.g. a per-account
transaction ledger — see `references/mcp-vs-browser.md`), never merely
because the token expired.

A background job caches its token at *its own* startup; a main-session
restart does not refresh a background job's token — kill + re-dispatch it.

**Trigger to read [`references/authentication.md`](references/authentication.md):**

- Xero MCP tools return authentication/authorization errors
- Starting a Xero workflow and unsure if the token is current
- Token has expired (~30 minute lifetime)
- First-time setup, or after revoking and re-authorizing the Xero app

That reference covers the `xero-oauth` script, prerequisites (`.env`
credentials, Xero app registration), the refresh-vs-full-flow choice,
and which config files get updated.

## Searching for records

The MCP list-* tools paginate at 10 records per page. Absence on page
1 is **not** absence in Xero. Before concluding a record is missing,
search by ID directly or page exhaustively.

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
