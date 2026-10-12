# rotki API recipes

Verified against rotki 1.44.1. Paths are relative to
`http://127.0.0.1:<core-port>/api/1`. The authoritative reference is
`docs/api.rst` in the rotki repository; search it by route rather than
reading it whole.

## Reads

| Purpose | Request |
|---|---|
| Tracked accounts on a chain | `GET /blockchains/<CHAIN>/accounts` (no body, no JSON header) |
| History events | `POST /history/events` with filters: `location`, `location_labels`, `identifiers`, `tx_refs`, `group_identifiers`, `event_subtypes`, `from_timestamp`, `to_timestamp`, `limit`, `offset`, `aggregate_by_group_ids: false` |
| Newest saved transaction per chain and address | `GET /blockchains/transactions/latest` |
| Undecoded transaction counts | `GET /blockchains/transactions/decode` with `{"async_query": false}` |
| Unmatched or ignored bridge legs | `GET /history/events/match/bridges?only_ignored=false\|true` |
| Candidate matches for a bridge leg (premium) | `POST /history/events/match/bridges` with `bridge_event`, `time_range` (seconds), `only_expected_assets`, `tolerance` |
| Internal-transaction conflicts | `GET /blockchains/transactions/internal/conflicts` with `failed`, `fixed`, `chain`, `limit`, `offset` |
| Premium tier and capabilities | `GET /premium/capabilities` |
| Manual balances | `GET /balances/manual` |

`POST /history/events` returns `result.entries`, each either an object or
a list of objects (grouped events), with the event under `.entry`.
Timestamps are milliseconds.

## Writes (each needs the user's approval)

| Purpose | Request | Undo |
|---|---|---|
| Add a transaction by hash, fetched from RPC nodes first | `GET /blockchains/evm/transactions/lookup` with `tx_hash`, `evm_chain`, `related_address` (a tracked address) | delete the transaction |
| Decode everything pending on a chain | `POST /blockchains/transactions/decode` with `chain` | n/a |
| Re-decode (and re-fetch) specific hashes | `PUT /blockchains/transactions/decode` with `chain`, `tx_refs`, `delete_custom: false` | re-decode again |
| Fetch transactions for chosen accounts | `POST /blockchains/transactions` with `accounts: [{address, blockchain}]`, time range | n/a |
| Add accounts | `PUT /blockchains/<CHAIN>/accounts` with `accounts: [{address, label}]` | `DELETE` same route |
| Match, ignore, mark external, or synthesise a bridge counterpart | `PUT /history/events/match/bridges` with `bridge_event` plus `matched_events`, nothing, `external: true` or `create_counterpart: true` | `DELETE` with `identifier` |
| Edit an event | `PATCH /history/events` with the full entry read back from `POST /history/events`, fields changed (e.g. `event_subtype: "donate"`, `user_notes`) | patch back |
| Add a manual balance | `PUT /balances/manual` with `balances: [{asset, label, amount, location, balance_type}]` | `DELETE` by identifier |

The lookup response's `was_fetched` is false when rotki already had the
transaction, which distinguishes new hashes from ones already present.
`delete_custom: false` keeps user-edited events when re-decoding.

To edit an event read back from `POST /history/events`, drop
`actual_group_identifier` before sending it to `PATCH /history/events`. If
the event shares a transaction with a matched asset movement, the read-back
`group_identifier` is the match's and the edit fails with "already exists";
use `actual_group_identifier` as `group_identifier` instead.

Spoof or poisoning addresses can be named in the private address book
(`PUT /names/addressbook/private` with `entries: [{address, blockchain,
name}]`) so rotki labels them wherever they appear; on-chain events from
them can be tagged with the `spam` subtype.
