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
never copy a refresh token anywhere else, and never edit or delete the
file (or its `.lock`) while agents are running.

## Multiple agents sharing the token file

Every agent host (each Claude Code session, Pi, OpenCode) starts its own
server process, and all of them share the one token file.

- **Access token (~30 min): sharing is harmless.** It is a bearer
  credential that any number of processes can use at once. Each server
  re-reads the file on every tool call, so it always uses the newest
  access token, even one another agent just fetched.
- **Refresh token: single-use, so refreshing is serialised.** A server
  refreshes only when the stored access token has under 5 minutes left.
  It then:
  1. takes the lock by creating `<token file>.lock` with O_EXCL (only
     one process can); others poll every 100 ms, for up to 45 s;
  2. **re-reads the file under the lock** — if another agent refreshed
     while it waited, it just uses that token and makes no Xero call,
     so each expiry causes exactly one refresh however many agents
     notice it;
  3. calls Xero, writes the new token pair to a unique 0600 temp file,
     fsyncs, and renames it over the token file (readers never see a
     half-written file);
  4. deletes the lock.
- **Within one server**, concurrent tool calls share a single in-flight
  refresh.
- **`xero-oauth`** uses the same lock, so running it while agents are
  active is safe.
- **Crashed holder:** a lock older than 60 s is treated as abandoned and
  broken. The refresh request times out after 20 s, so a live holder
  never gets near that.
- **Failed save** (disk full, permissions): that server keeps the rotated
  token in memory and prints a warning, so the only valid refresh token
  is not lost. Its session keeps working; after it exits, the full OAuth
  flow is needed.

Verified 2026-09-23 against live Xero: 6 processes × 20 locked
read-modify-write cycles lost no updates, and 3 servers hitting the same
expired token at once all succeeded with the refresh chain intact.

Not verified: whether Xero revokes an old access token as soon as a new
one is issued. The design does not rely on it (each call reads the
newest token first); at worst a request already in flight during a
refresh fails once and succeeds on retry.

**Rate limits are shared too.** All agents use the same Xero app and
organisation. Firing ~10 calls at once has returned "Too many requests
to Xero" for some of them: avoid fanning out many parallel Xero calls
(e.g. across subagents), and retry a rate-limited call after a moment
rather than treating it as an auth failure.

### Checking that self-refresh is working

```bash
jq '._obtained_at | todate' ~/.config/xero-mcp/tokens.json
```

shows when the current access token was minted (UTC). If that is later
than the last manual `xero-oauth` run, a server refreshed it by itself.
It moves forward roughly every 25–30 minutes while agents are making
Xero calls, and stands still while idle (the next call refreshes).

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
