# Xero MCP Authentication (self-refreshing token file)

The Xero MCP server runs in `XERO_TOKEN_FILE` mode (upstream PR #200 plus
local locking fixes; see [`local-server.md`](local-server.md)). It reads
an OAuth2 token store from disk on **every tool call**, refreshes the
~30-minute access token itself when it is near expiry, and writes the
rotated refresh token back. **No agent restart is ever needed for
tokens.**

## Configuration

`.mcp.json` / `opencode.json` run the server as
`node --env-file=/home/adam/finance/.env <server>/dist/index.js`, so no
token or secret lives in a tracked file. `.env` (gitignored) holds:

```
XERO_CLIENT_ID=<your-xero-app-client-id>
XERO_CLIENT_SECRET=<your-xero-app-client-secret>
XERO_TOKEN_FILE=/home/adam/.config/xero-mcp/tokens.json
XERO_TENANT_ID=<tenant id printed by xero-oauth>
```

Keep `XERO_TENANT_ID` set: without it the server writes to whichever
connected organisation Xero lists first.

The token file (0600, in a 0700 directory) is the **single source of
truth** for the refresh token. Xero rotates the refresh token on every
use and only honours the previous one for a 30-minute grace period, so
never copy a refresh token anywhere else. Every writer (the server and
`xero-oauth`) holds the `<token file>.lock` O_EXCL lock while it
reads, refreshes and writes, so several servers (Claude Code, Pi,
OpenCode) can share the file safely.

## When to run `xero-oauth`

Almost never. Only:

- **First-time setup, or after revoking the Xero app** — full OAuth
  flow (browser).
- **Changing scopes** — full OAuth flow; a refresh keeps the original
  scopes.
- **The refresh token has expired** — unused refresh tokens expire after
  60 days, e.g. if no Xero MCP call was made for two months. Symptom:
  every tool call fails authentication and a manual `--refresh` fails
  too. Needs the full OAuth flow.

A tool call failing authentication is **not** by itself a reason to
refresh: the server already refreshes on demand. Check the failure
first — a scope the token lacks (e.g. `list-journals` needs
`accounting.journals.read`) also reports "Authentication failed".

## Script

The implementation lives at [`../scripts/xero-oauth`](../scripts/xero-oauth)
within this skill directory. The `ai-config` repo also keeps a
`bin/xero-oauth` symlink pointing at it; stowing the repo (`mr restow`)
places that symlink on `PATH` as `~/bin/xero-oauth`. Run it from the
project directory containing `.env`.

```bash
xero-oauth           # full OAuth flow, read-only scopes (browser required)
xero-oauth --write   # full OAuth flow, read+write scopes
xero-oauth --refresh # rotate the stored refresh token now (no browser)
```

Each writes the token file under the lock and prints the connected
organisations with their tenant IDs.

**Run it bare and read the output in full** — never crop it with `tail`,
`head`, `grep` etc. Success, failure and warnings are spread across the
output, and a cropped fragment has previously been misreported as a
successful refresh.

The full flow opens a local server on port 8080 and waits for the browser
callback; the Xero app at <https://developer.xero.com/app/manage> must
list `http://localhost:8080/callback` as a redirect URI.

> If the browser auto-connects without showing the org selector, revoke first:
> Xero → 3×3 dot icon (top right) → **Manage connected apps** → disconnect,
> then re-run.

## Scopes

The token carries the scopes in `xero-oauth`'s `ACCOUNTING_SCOPES_RW`
list. Tools from newer PRs need scopes it does not request, and fail
until a full `--write` flow is re-run with the extra scopes added:

- attachments tools (#109): `accounting.attachments.read`
- `list-journals` / `get-journal` (#298): `accounting.journals.read`
  (Xero may require approval before granting it)
