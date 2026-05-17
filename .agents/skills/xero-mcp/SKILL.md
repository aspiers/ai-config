---
name: xero-mcp
description: Use the Xero MCP server — obtain/refresh OAuth2 bearer tokens, troubleshoot authentication, and pick up other operational notes for working with Xero MCP tools. Use when Xero MCP tools fail with authentication errors, when the bearer token has expired (tokens last ~30 min), before starting any Xero workflow, or for general guidance on Xero MCP usage.
---

# Xero MCP

Covers usage of the Xero MCP server, including authentication
(OAuth2 bearer tokens) and related operational notes.

For browser-driven automation of the Xero web UI (not via MCP), see the
separate [`xero-browser`](../xero-browser/SKILL.md) skill instead.

## Authentication (OAuth2 bearer tokens)

The Xero MCP server requires a valid bearer token
(`XERO_CLIENT_BEARER_TOKEN`) in its environment. Tokens last ~30 minutes;
refresh before or after expiry using the script below.

### When to (re)authenticate

- Xero MCP tools return authentication/authorization errors
- Starting a Xero workflow and unsure if the token is current
- Token has expired (~30 minute lifetime)
- After revoking and re-authorizing the Xero app

### Script

The implementation lives at [`scripts/xero-oauth`](scripts/xero-oauth)
within this skill directory. Either invoke it by absolute path, or
symlink it onto your `PATH`:

```bash
ln -s ~/.claude/skills/xero-mcp/scripts/xero-oauth ~/bin/xero-oauth
```

All commands below assume `xero-oauth` resolves on `PATH`. Run from a
project directory that has `.env`, `opencode.json`, and/or `.mcp.json`
in its working directory — the script always reads/writes those at
`$PWD`.

### How it works

`xero-oauth` reads credentials from `.env` and writes:

- The new `access_token` into both
  `opencode.json` → `mcp.xero.environment.XERO_CLIENT_BEARER_TOKEN`
  (used by OpenCode) and
  `.mcp.json` → `mcpServers.xero.env.XERO_CLIENT_BEARER_TOKEN`
  (used by Claude Code's project-level MCP config)
- The new `refresh_token` back into `.env` → `XERO_REFRESH_TOKEN`

Both files are updated whether you use Claude Code, OpenCode, or both —
no configuration switch is required.

After running, **restart the agent session** to pick up the new token.

### Prerequisite

Register your own Xero OAuth2 app at
<https://developer.xero.com/app/manage> with redirect URI
`http://localhost:8080/callback`. Then `.env` (gitignored) must
contain:

```
XERO_CLIENT_ID=<your-xero-app-client-id>
XERO_CLIENT_SECRET=<your-xero-app-client-secret>
XERO_REFRESH_TOKEN=<refresh-token>   # only needed for --refresh
```

### Usage

#### Token refresh (no browser — preferred)

Use when `XERO_REFRESH_TOKEN` is already in `.env`:

```bash
xero-oauth --refresh
```

#### Full OAuth flow (browser required)

Use for first-time authorization or after revoking the app:

```bash
xero-oauth          # read-only scopes (default)
xero-oauth --write  # read+write scopes
```

Opens a local server on port 8080, prints an authorization URL, and waits
for the browser callback. The script updates `opencode.json`, `.mcp.json`,
and `.env` automatically once the flow completes.

By default, only read-only OAuth scopes are requested. Pass `--write` to
request read+write scopes (needed for creating/updating invoices, contacts,
bank transactions, manual journals, etc.).

> If the browser auto-connects without showing the org selector, revoke first:
> Xero → 3×3 dot icon (top right) → **Manage connected apps** → disconnect,
> then re-run.

### After running

Restart the agent session (Claude Code or OpenCode) so the new
`XERO_CLIENT_BEARER_TOKEN` is picked up by the Xero MCP server.
