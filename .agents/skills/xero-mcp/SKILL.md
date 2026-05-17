---
name: xero-mcp
description: Use the Xero MCP server — obtain/refresh OAuth2 bearer tokens, troubleshoot authentication, and pick up other operational notes for working with Xero MCP tools. Use when Xero MCP tools fail with authentication errors, when the bearer token has expired (tokens last ~30 min), before starting any Xero workflow, or for general guidance on Xero MCP usage.
---

# Xero MCP

Covers usage of the Xero MCP server, including authentication
(OAuth2 bearer tokens) and related operational notes.

For browser-driven automation of the Xero web UI (not via MCP), see the
separate [`xero-browser`](../xero-browser/SKILL.md) skill instead.

## Authentication

The Xero MCP server needs a valid bearer token
(`XERO_CLIENT_BEARER_TOKEN`) in its environment. Tokens last ~30 minutes
and must be refreshed via the `xero-oauth` helper script.

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
