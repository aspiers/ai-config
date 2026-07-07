# Xero: MCP vs browser — which to use

Single source of truth, shared by the `xero-mcp` and `xero-browser`
skills. Pick the tool by the **shape of the data**, not by which is
already open.

| Need | Use | Why |
|------|-----|-----|
| **A single account's full transaction ledger** — every line incl. bills / spend-money / Cryptio-synced bank txns, with a running balance | **BROWSER** — Account Transactions report (`xero-browser` → "Searching Transactions By Date Range") | Xero MCP has **NO per-account transaction endpoint**. `list-manual-journals` returns ONLY manual journals — it misses bills and the bulk of a wallet/asset account's movement. |
| **One record by known UUID** — a specific manual journal, invoice, bill | MCP `list-manual-journals manualJournalId=<uuid>` (or `list-invoices` etc.) | Direct fetch, no pagination. |
| **Create / update / void a manual journal** | MCP write tools (`xero-mcp` → "Manual journals") | Faster than the browser Edit flow; void-and-replace works via MCP. |
| **Balance sheet / P&L / trial balance / aged payables/receivables** | MCP `list-report-*` / `list-trial-balance` | Purpose-built report endpoints. (Note `list-trial-balance` output can exceed the tool's token limit — it spills to a file; grep that. `list-report-balance-sheet` is compact.) |
| **Search narrations / free-text across journals** | **BROWSER** — Account Transactions Filter (`xero-browser` → "Searching Transactions By Description") | The global Xero Search bar does NOT search manual-journal narrations. |

## Anti-pattern — do NOT do this

**Paginating ALL of `list-manual-journals`** (10/page, ~13+ pages for the
Toucan tenant) to reconstruct one account's ledger. It spams the MCP
server, misses non-MJ lines (bills etc.), and the browser Account
Transactions report gives the complete authoritative ledger in a single
pull. If you find yourself looping `page=1,2,3,…` to rebuild an account,
STOP and use the browser report.

The only legitimate full pagination of `list-manual-journals` is when you
genuinely need to enumerate MANUAL JOURNALS specifically (not an account
ledger) and have no UUID to fetch directly — rare. Even then, prefer the
browser report filtered to the relevant account if you're after ledger
movement.

## One-line heuristic

- **"What's in this account?"** → browser Account Transactions report.
- **"Fetch/verify/change this specific journal"** or **"what's the balance/report?"** → MCP.
