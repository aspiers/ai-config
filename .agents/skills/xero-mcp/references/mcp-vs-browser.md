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
| **Unreconciled bank statement lines** (what's waiting in the reconcile screen) | **BROWSER** — `/BankRec/BankRec.aspx?accountID=<bank account uuid>` | The Accounting API only exposes booked transactions; `list-bank-transactions` cannot see feed lines. Statement lines need the Finance API (`BankStatementsPlus`), whose scope is restricted (developer-terms addendum) and absent from our token. Checked 2026-10-06. |
| **Approve, delete or void an invoice/bill** | MCP `update-invoice` with only `status` (`AUTHORISED` / `DELETED` / `VOIDED`) | Added by upstream PR #221 in the local build. Verified 2026-10-06 (approve, delete a draft, void an unpaid bill). Send `DELETED`/`VOIDED` alone; Xero ignores other fields with them. Still refused inside an adviser lock. |
| **Supplier credit note** (e.g. reversing a bill in a locked period) | **BROWSER** — Bill Options → Add Credit Note (`xero-browser` → "Reversing a locked bill with a supplier credit note") | MCP `create-credit-note` hard-codes a sales `ACCRECCREDIT`, `DRAFT`, today, base currency. `create-credit-note-allocation` and `list-credit-notes` do handle supplier credit notes. |
| **Did a bank line clear a bank account?** (balance check) | MCP `list-report-balance-sheet` | Its bank row is Xero's balance; compare with the statement balance shown on the BankRec page. Equal means nothing unreconciled. |

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
