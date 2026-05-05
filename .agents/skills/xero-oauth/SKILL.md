---
name: xero-oauth
description: Obtain or refresh a Xero OAuth2 bearer token to establish an active Xero MCP session. Use when Xero MCP tools fail with authentication errors, when the token has expired (tokens last ~30 min), or before starting any Xero workflow.
---

# Xero OAuth

Ensures the Xero MCP server has a valid bearer token.

## Script

The implementation lives at [`scripts/xero-oauth`](scripts/xero-oauth)
within this skill directory. Either invoke it by absolute path, or
symlink it onto your `PATH`:

```bash
ln -s ~/.claude/skills/xero-oauth/scripts/xero-oauth ~/bin/xero-oauth
```

All commands below assume `xero-oauth` resolves on `PATH`. Run from a
project directory that has `.env`, `opencode.json`, and/or `.mcp.json`
in its working directory — the script always reads/writes those at
`$PWD`.

## When to Use

- Xero MCP tools return authentication/authorization errors
- Starting a Xero workflow and unsure if token is current
- Token has expired (they last ~30 minutes)
- After revoking and re-authorizing the Xero app

## How It Works

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

## Prerequisite

Register your own Xero OAuth2 app at
<https://developer.xero.com/app/manage> with redirect URI
`http://localhost:8080/callback`. Then `.env` (gitignored) must
contain:

```
XERO_CLIENT_ID=<your-xero-app-client-id>
XERO_CLIENT_SECRET=<your-xero-app-client-secret>
XERO_REFRESH_TOKEN=<refresh-token>   # only needed for --refresh
```

## Usage

### Token refresh (no browser — preferred)

Use when `XERO_REFRESH_TOKEN` is already in `.env`:

```bash
xero-oauth --refresh
```

### Full OAuth flow (browser required)

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

## After Running

Restart the agent session (Claude Code or OpenCode) so the new
`XERO_CLIENT_BEARER_TOKEN` is picked up by the Xero MCP server.
