---
name: rotki-api
description: Drives a running rotki desktop app through its local REST API and MCP server, and explains rotki's EVM indexer coverage (Etherscan, Blockscout, Routescan free and paid tiers), bridge-transaction matching, internal-transaction conflicts and zkSync Lite quirks. Use when querying or changing rotki data from an agent, when rotki warns that an indexer or paid API key is needed, when chains such as Base, BSC, Optimism, Polygon or zkSync Lite are missing transactions, when matching bridge legs, when resolving "Internal Transaction Conflicts", or when deciding whether to use rotki's MCP server.
---

# rotki API

rotki keeps a user's whole crypto accounting history. Every write changes
their books, so **get explicit approval for each write** (adding accounts,
matching or ignoring bridge legs, re-decoding, editing events, manual
balances), naming the endpoint, the effect and how to undo it. "Help me
match these" is a request for help, not approval. Reads need no approval.

## Reaching the backend

The desktop app's launcher (`starling`) runs the core and passes its ports
on the command line, so read them from the process instead of guessing:

```bash
ps -eo args | grep '[s]tarling'   # --core-port, --mcp-port, --proxy-port
```

The core API is `http://127.0.0.1:<core-port>/api/1/` (4242 by default),
with no authentication on the desktop. A user must be logged in.

Request quirks that cost time:

- Many GET endpoints take a JSON body, but a `Content-Type: application/json`
  header on a GET **without** a body returns HTTP 500 ("400 Bad Request:
  The browser (or proxy) sent a request...").
- Doc headings sometimes show a trailing slash (`/balances/manual/`); the
  real route has none and the slash gives 404.
- `POST /history/events` rejects `async_query`; most other endpoints accept
  it.
- Chain names differ by endpoint: the accounts path uses the
  `SupportedBlockchain` value (`BASE`, `BINANCE_SC`, `POLYGON_POS`,
  `ZKSYNC_LITE`), lookup and decode use lowercase chain names (`base`,
  `binance_sc`, `zksync_lite`), and history-event `location` filters use
  labels with spaces (`polygon pos`, `binance sc`, `zksync lite`).

For the endpoints used most and their payloads, read
[references/api-recipes.md](references/api-recipes.md).

## Missing transactions and indexer keys

rotki lists an address's transactions only through Etherscan, Blockscout
or Routescan, and the free tiers no longer cover several chains. Before
recommending a paid plan, read
[references/indexers-and-gaps.md](references/indexers-and-gaps.md): it
gives per-chain coverage, how to prove what is actually missing, and a
free route that feeds hashes from another source into rotki's lookup
endpoint, which fetches each transaction from RPC nodes.

## Bridge matching

The destination of an unmatched bridge leg is in the event's
`extra_data.bridge.to_chain` and `to_address`; read it before searching
time windows. Then pick the resolution by what really happened:

| Situation | Resolution |
|---|---|
| Counterpart exists in rotki | `PUT /history/events/match/bridges` with `matched_events` |
| Funds arrived but no transaction can ever be fetched: Polygon PoS deposits (credited by state sync, no transaction to the user), Optimism before the 11 Nov 2021 regenesis | `create_counterpart: true` (synthetic leg; unlinking deletes it) |
| Destination is the user's but untracked by rotki (e.g. Linea, chain 59144) | Ignore the leg (no `matched_events`), optionally add a manual balance |
| Funds really left the user | `external: true`, which books a payment and therefore a disposal |

Ignoring keeps the move a transfer; `external` changes the accounting.
Finding and changing matches needs premium; listing unmatched legs does not.

## Internal transaction conflicts

`all_zero_gas` means every stored internal-transaction row for a parent
transaction has `gas = '0'`, so rotki cannot tell good rows from bad
duplicates and wants to repull. "Resolve Selected" only repeats the repull
through the same indexers, so it keeps failing where no free indexer
serves the chain or era. Check the decoded amounts against an independent
source; if they agree, the conflict is harmless to the books.

## zkSync Lite

- Adding a second zkSync Lite account fetches nothing if its history is
  older than the newest transaction already saved for any account:
  `fetch_transactions()` starts from a database-wide maximum
  ([rotki/rotki#13345](https://github.com/rotki/rotki/issues/13345)).
  Work around it by re-decoding the missing hashes with
  `PUT /blockchains/transactions/decode`, `chain: zksync_lite`, which
  fetches each by hash. Get the hashes from
  `https://api.zksync.io/api/v0.2/accounts/<address>/transactions?from=latest&limit=100&direction=older`.
- rotki has no zkSync Lite decoders for protocols such as Gitcoin's 2020
  zkSync checkout; transfers appear as plain spends to retag by hand.

## Decode-time context

Events are labelled with the accounts tracked when they were decoded. A
transfer decoded before its other side's account was added stays a plain
receive or spend (possibly income) until that hash is re-decoded.

## Secrets in rotki errors

Blockscout errors embed the full request URL, including `apikey=`, in
notifications, logs and the conflicts table's `last_error`
([rotki/rotki#13346](https://github.com/rotki/rotki/issues/13346)).
Redact `apikey=` from any rotki output before saving or quoting it.

## MCP server

rotki 1.44+ ships a local, **read-only** MCP server (premium capability
`mcp`, check `GET /premium/capabilities`). It offers SQL over a snapshot
of history events and balances, asset details, cached historical prices
and the event taxonomy. It cannot change anything, so fixes still go
through the REST API. Its default `balanced` privacy mode hashes
addresses and transaction hashes, which suits analysis but not debugging
specific transactions. The user starts it from Settings → MCP, which
shows the endpoint; the launcher's `--mcp-port` gives the port.
