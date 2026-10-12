# Indexer coverage and missing transactions

State as verified in October 2026 with rotki 1.44.1. Tiers change, so
re-check the providers' pages before telling a user what to buy.

## Why indexers at all

A node answers "give me transaction X" but has no address index, so it
cannot answer "which transactions involve address A?". rotki uses
indexers for that list, and for internal transactions, which need trace
APIs that free public nodes rarely offer.

## Coverage per chain in rotki 1.44.1

| Chain | rotki's default order | Free option |
|---|---|---|
| Ethereum | Etherscan, Blockscout, Routescan | free Etherscan key |
| Polygon PoS | Etherscan first | free Etherscan key (Blockscout dropped Polygon from its free tier) |
| Arbitrum One | Etherscan first | free Etherscan key |
| Optimism | Blockscout, Etherscan | free Blockscout PRO key, but Blockscout skips internal transactions before Bedrock (June 2023); Etherscan is paid-only |
| Base | Blockscout, Etherscan | none: Blockscout answers HTTP 402 for a free key, Etherscan is paid-only |
| Gnosis | Blockscout, Etherscan | free Blockscout key |
| BNB Smart Chain | Etherscan only | none: Etherscan is paid-only, no other indexer |
| Celo, Linea | not supported by rotki | n/a |

Sources: rotki `rotkehlchen/chain/evm/types.py` (`DEFAULT_INDEXERS_ORDER`),
[Etherscan supported chains](https://docs.etherscan.io/supported-chains)
(free or paid per chain) and [Etherscan API plans](https://etherscan.io/apis)
(cheapest paid plan "Lite"). Etherscan "Premium" is a website subscription
(name tags, no ads) with no stated API benefit. Its terms forbid scraping
the explorer sites.

## Free route for chains with no free indexer

Get the hashes elsewhere and hand each to rotki's lookup endpoint
(`GET /blockchains/evm/transactions/lookup`), which fetches the
transaction and receipt from RPC nodes before any indexer. Alchemy's
`alchemy_getAssetTransfers` is free (30M compute units a month) on Base,
BNB Smart Chain, Polygon and Optimism; each network must be enabled on the
Alchemy app, or it answers 403 "<NETWORK> is not enabled for this app".
Its `internal` category works only on Ethereum, Polygon and Base. Query
`fromAddress` and `toAddress` separately and follow `pageKey`.

Gap: rotki still fetches a hash's internal transactions through its
indexers, so native coins sent by contracts may lack amounts.

## Proving what is missing

Compare rotki's newest transaction per address
(`GET /blockchains/transactions/latest`) with an independent source such
as Alchemy, then list the newer transfers. Classify them before acting:
inbound-only ERC-1155/721 transfers and unsolicited ERC-20 deposits are
usually spam airdrops that rotki does not record, not missing activity.
Outgoing or native transfers missing from rotki are real gaps.

## Identify tokens by contract, never by symbol

Address-poisoning campaigns send dust from addresses that copy the first
and last characters of a real counterparty, and fake token contracts emit
forged `Transfer` events naming the victim, with symbols such as "USDC" or
lookalike Unicode. Such entries show up as spends in Alchemy results and in
rotki. Before calling a transfer real, check the token contract and who
signed the transaction (`eth_getTransactionByHash` → `from`); then offer to
add the fake token to ignored assets and name the lookalike in the private
address book.
