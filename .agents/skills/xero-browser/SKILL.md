---
name: xero-browser
description: General Xero browser automation notes. Use when automating any Xero page with agent-browser — covers non-standard UI patterns, waiting, and dropdown menus.
---

# Xero Browser Automation

General notes for automating Xero with `agent-browser`.
Load [`agent-browser-local`](../agent-browser-local/SKILL.md) alongside this
skill for cross-site viewport, stale-ref, tab-safety, waiting, and widget
guidance.

For Xero MCP server usage (OAuth, list-* tools, searching records by ID
vs. pagination), see the separate [`xero-mcp`](../xero-mcp/SKILL.md)
skill instead.

## MCP vs browser — which to use (READ FIRST)

**Before any Xero data task, read [`../xero-mcp/references/mcp-vs-browser.md`](../xero-mcp/references/mcp-vs-browser.md).**
It is the single source of truth for choosing MCP tools vs the browser
Account Transactions report (shared with the `xero-mcp` skill — do not
duplicate its content here). Key rule: Xero MCP has **no per-account
transaction endpoint**, so a single account's full ledger comes from the
browser Account Transactions report (see "Searching Transactions By Date
Range" below), never from paginating `list-manual-journals`.

## Fiduciary Responsibility

This is accounting with fiduciary responsibility. **Always stop and report
any discrepancy** — in amounts, dates, accounts, or anything that doesn't
match expectations — rather than assuming it is "likely fine".
Do not proceed past a discrepancy — surface it to the user immediately.

**CRITICAL: Never delete anything in Xero without explicit user permission.**
This includes invoices, bills, payments, bank transactions, contacts,
manual journals, attachments, reconciliations, and any other record or
artifact. If deletion seems like the cleanest fix, stop and ask first.

## Verifying write operations — READ THE PAGE, don't grep past the error

**A click that reports `✓ Done` proves nothing.** `agent-browser click`
reports success when it dispatched the click, NOT when Xero accepted the
change. Xero frequently renders a **refusal as ordinary page text** rather
than an exception, so the automation layer sees nothing wrong.

**After every write (void, edit, post, reconcile, delete), you MUST:**

1. **Read the page unfiltered** — `agent-browser snapshot` with NO grep, or
   grep that explicitly INCLUDES `error|reason|locked|cannot|denied|invalid`.
   A grep written only for the expected *success* text will silently filter
   the error out of your own view.
2. **Independently confirm the new state**, ideally via MCP
   (`list-invoices invoiceNumbers=[...]`) — check `Status` AND `Last Updated`.
   An unchanged `Last Updated` means the write never landed.

**Never invent an explanation for a failed write before reading the page.**

**Evidence (2026-07-17):** voiding a bill — Bill Options → Void →
confirmation dialog → OK. Every click reported `✓ Done`, a real dialog
appeared. The bill was unchanged. The agent grepped for
`void|status|awaiting`, saw nothing, and fabricated a stale-ref theory. Xero
had rendered the actual reason on the page all along:

> An error occurred for the following reason:
> • Your accounts are locked by your adviser up until &lt;date&gt;.
> Your action must occur after this date.

### Period lock (adviser lock) — a common silent refusal

An adviser/accountant can **lock the books up to a date**. Any write to a
record dated *before* that lock date is refused with the message above, no
matter how correct the action is. This blocks void, edit, delete, and payment
changes alike.

- **Check the record's DATE against the lock before attempting a write.** A
  bill dated in a locked period cannot be voided, full stop.
- Standard remedies, all requiring the user's decision: a **credit note
  dated after the lock date** to reverse it; asking the adviser to lift the
  lock; or leaving the record and adding a **note** explaining it.
- Do NOT retry the same write, and do NOT look for a way around the lock —
  it is a deliberate accounting control, not a UI bug.

## Authentication / Login

The browser session **must already be logged in to Xero** before any of the
report/automation workflows below will work. Otherwise `go.xero.com` simply
redirects to `login.xero.com`.

- **Browser-session login** (the relevant kind here): use the `agent-browser
  auth` subcommand with the saved `xero` credential profile, if available. Run
  `agent-browser auth login xero` — it waits for the login form fields, fills
  them, and submits. (`agent-browser auth list` shows the available profiles;
  a `xero` profile already exists. A profile is created in the first place
  with `agent-browser auth save`.) After login, **wait a few seconds** for the
  OIDC redirect to settle, then verify with `agent-browser eval
  "location.href"` — it should land on the `go.xero.com` app homepage, not
  `login.xero.com`.
- **Xero MCP/API auth** (OAuth bearer tokens) is a **separate** thing, covered
  by the [`xero-mcp`](../xero-mcp/SKILL.md) skill and its [authentication
  reference](../xero-mcp/references/authentication.md).  MCP-token auth is
  **not** the same as browser-session login: a fresh browser still needs its
  own login even when the MCP tools work.

### "Access Denied" / 404 error pages mid-session → hand off to user for manual login

If, during a session, a page lands on an Akamai **"Access Denied"**
edge-block (`errors.edgesuite.net`, `Reference #...`) or an
`/app/.../errors/404` page — even after a seemingly successful login —
the browser session has lost its Xero auth. **Do NOT try to re-auth
yourself.** Stop, and prompt the user to intercede and manually log in
at **<https://login.xero.com/>**. Wait for them to confirm login is
complete, then re-verify with `eval "location.href"` — it should land
on `go.xero.com/app/...`, not `login.xero.com`. Do not treat these
error pages as a dead end or switch to a workaround; hand off and wait.

**2FA is part of this and is the user's step.** Manual login usually
routes through a `login.xero.com/.../two-factor/authenticate` page. Do
NOT try to complete 2FA yourself — it is entirely the user's to do.
After a successful login+2FA the URL settles on `go.xero.com/app/...`.

## Waiting

Apply the general waiting guidance from `agent-browser-local`. Xero's
persistent background requests never reach network idle, so use a concrete
state or fixed wait instead. **~3 s (`wait 3000`) is the ceiling, not the
default** — for most in-app interactions (menu open, picker toggle,
snapshot after a click) 1–2 s is plenty; reserve 3 s for full report
re-renders after `Update`. Waiting more than 3 s to "let a page settle"
is overkill.

## Searching Transactions By Description / Free Text

**The global Xero Search bar (top nav) does NOT search manual-journal
narrations.** Verified 2026-05-04: searching for a hash that is the literal
text of a posted journal narration returns "No results found".

To search narrations, use the Account Transactions report's
**Filter button** instead. (The screenshots and steps below assume the
standard `Account Transactions` report under `Reporting`. If you have
a saved custom variant — e.g. with grouping disabled and extra
columns added — use that instead; the workflow is identical.)

### Workflow

1. Navigate to `https://go.xero.com/app/dashboard`, then `Reporting` →
   `Account Transactions`. Wait for the report to render.
2. (Optional) Expand to all 202 accounts via the Accounts picker if you
   want a global narration search rather than one constrained to a few
   accounts. See "Searching Transactions By Date Range" below.
3. Click the `Filter` button in the toolbar.
4. In the Filter dialog, the `Description` row is initially **collapsed**
   and its inner Contains textbox does **not yet exist** in the snapshot.
   Click on the `Description` row generic (e.g. `generic "Description"
   [ref=eN]` or, if a filter is already active, `generic
   "Description0xprefix..." [ref=eN]`) to expand it. After expanding,
   re-snapshot — a `textbox "Contains" [ref=eM]` now appears inside that
   row.
5. Fill the `Contains` textbox (the **inner** one, not the dialog's
   top-level "Search filters" box) with the search string, e.g. a tx
   hash prefix like `0x4c1dcbad`.
6. Click `Apply 1 filter` to close the dialog.
7. **Click `Update`** afterwards to actually re-render the report.
   Apply alone does NOT re-render; the previous filter state remains
   active until Update fires.
8. After re-render, the report shows either matching rows or
   `Nothing to show here` (no hits — equivalent to "no results").

### Pitfalls

- The Filter dialog has a top-level `Search filters` textbox at the top
  (`textbox "Search filters" [ref=...]`). It filters the *list of
  available filter types* (Account, Date, Description, etc.), **not the
  report data**. Filling it and clicking Apply produces "No filters
  found" and has no effect on the report.
  - When grep'ing snapshot output for a textbox to fill, this top box
    matches `textbox "Search filters"` while the right inner one
    matches `textbox "Contains"`. Always target `"Contains"` exactly,
    and expand the Description row first (otherwise no Contains box
    exists yet and grep will fall through to other refs).
- Re-opening the Filter dialog when a Description filter is already
  active shows the row collapsed with its current value embedded in the
  generic label (e.g. `generic "Description0xafe067de"`). It does NOT
  auto-expand. You have to click it to expose the inner Contains
  textbox.
- After Apply closes the dialog, the dialog's `Apply 1 filter` button
  count changes to reflect filter state — use that to verify the filter
  was registered.
- Looping through many filter values: after each Update, wait 6+ seconds
  before the next iteration. Re-snapshot after every step — refs
  change. Verify each iteration with a screenshot or by grepping the
  saved snapshot for `Nothing to show here` vs hash prefix matches.

### Use cases

- Cross-checking whether a specific transaction (e.g. an on-chain tx
  identified by hash, or any other narration string) is already booked
  in Xero. When the source system's displayed timestamp can drift from
  the canonical event time (as with on-chain transactions and tools like
  Cryptio that reflect ingestion time rather than block time),
  date+amount matching is unreliable — match on a canonical identifier
  embedded in the journal narration instead.

## Searching Transactions By Date Range

When you need to find transactions within a specific date range, use the
custom `Account Transactions` report rather than browsing journals
or bank pages one by one.

### Workflow

1. Navigate to `https://go.xero.com/app/dashboard` as the stable entry point,
   then open `Reporting` from the top navigation. Do not construct org-scoped
   URLs like `/app/<orgcode>/reporting` by hand — the org code changes and
   typing the wrong one hits a "You don't have access to this organisation"
   page.
2. Open `Account Transactions`.
3. Configure `Grouping/Summarising`.
4. Open the menu.
5. Set `Grouping/Summarising` to `None` unless you explicitly need grouped totals.
6. Confirm the change.
7. Close the menu.
8. If you deliberately keep grouping enabled, consider `Accounts to include = Only with transactions` to remove empty-account sections.
9. Configure the Accounts picker deliberately.
10. Decide whether you want the broadest report or a narrow report.
11. If you want the broadest report, open the Accounts picker, click `Select all`, confirm the selected-account count, and close the picker.
12. If you want a narrow report, first take a snapshot.
13. Open the Accounts picker.
14. Take another snapshot with the picker open.
15. If needed, reset the hidden selection state first by clicking `Select all` and then `Deselect all`.
16. For each account you want to include, use the ref from the open-picker snapshot for that account row, `scrollintoview` that ref, then `check` the checkbox ref.
17. If the DOM changes enough that refs may have been reassigned, take another snapshot with the picker still open before continuing.
18. Confirm the final selected-account count.
19. Close the picker.
20. Open the `Columns` menu.
21. Add `Account`, `Account Code`, and `Account Type` if they are not already selected.
22. Confirm the change.
23. Close the menu.
24. Set the start and end date fields directly. After filling **both** date
    fields you **must close the calendar picker before clicking Update** —
    press `Escape` or click off the field. Do not snapshot or interact with
    any other control between filling start and filling end. If you do
    anything between the two fills (especially a snapshot, which can
    re-render the picker), Xero may paste your end-date string into the
    start-date field and leave the end date untouched (end field stays at
    e.g. `1 Jan 9000`). Re-snapshot once after both fills and verify both
    fields display the expected value before clicking Update.
25. Click `Update`.
26. Read the transaction rows from the report table.

### Accounts picker: click the `[onclick]` wrapper, not the combobox

The Accounts picker trigger renders as **two stacked elements** in
`agent-browser snapshot -i`:

- an OUTER `generic "N accounts selected" [ref=eXX] clickable [onclick]`
  — **this** is the click target (it carries the onclick handler)
- an INNER `combobox "N accounts selected" [expanded=false, ref=eYY]`
  — inert; clicking it does **nothing** (stays `expanded=false`)

Click the **outer generic**, not the inner combobox. The `[onclick]`
marker in the snapshot is the tell for which ref to click. (Same rule
as elsewhere in this skill: click the ref that carries the handler for
the visible label, not a nested inert element.)

- **Toggle:** clicking the wrapper opens the picker; clicking it again
  (or `Escape`) closes it. After selecting, close it, then click `Update`.
- **Full list when open:** the open picker exposes the entire account
  list as `checkbox "1234 - Account Name" [checked=true|false, ref=...]`
  rows (plus a `Select all` button). Select the documented way —
  `scrollintoview @rowRef` then `check @checkboxRef`. **Do NOT** try to
  JS-match checkboxes by label text via `eval`: an attempt to bulk-check
  that way silently failed / returned NOT FOUND while the real checkbox
  refs were sitting right there in the snapshot.
- **Refs:** checkbox refs stay stable while the picker stays open across
  snapshots, but the **trigger's own wrapper ref changes** after the
  report re-renders — re-snapshot to get a fresh wrapper ref each time
  you open it.

### Notes

- Treat each report setting as a small closed loop: open, change, confirm, close, then move on.
- Do not leave `Grouping/Summarising`, `Columns`, or the account picker open while moving to another control.
- `Grouping/Summarising = None` is the preferred default because it removes extra grouping noise and makes individual ledger lines easier to scan.
- Setting `Grouping/Summarising` to `None` can trigger a `Missing settings info` button, but the report can still render rows after updating.
- The Accounts picker can be driven reliably from the full unfiltered list by combining `scrollintoview` with `check`.
- `scrollintoview` is the preferred way to bring a target account into view before checking it.
- Never put `snapshot` at the start of a single `&&` command chain and then continue with refs chosen in advance. That creates a mismatch: the refs in the later commands were selected before that newest snapshot ran.
- The safe pattern is: run `snapshot`, inspect its output, then build a later command using refs from that exact snapshot. If opening the picker or checking a box changes the DOM, snapshot again and use the new refs.
- The search-box method is still valid, but it is slower and should be treated as a fallback. See Appendix: Filtered Account Search Fallback.
- For a single day search, set both date fields to the same date.
- Date fields accept typed values such as `2 Dec 2024`.
- This report is useful for spotting transaction descriptions, journal numbers, related accounts, debit/credit values, and references on the chosen date.
- The default columns are typically not enough; strongly recommended to add `Account`, `Account Code`, and `Account Type` to make it easier to trace which ledger accounts were hit.
- Do not assume the default account selection is appropriate. Either expand to all accounts with `Select all` or deliberately narrow to specific accounts.

### Important

- Do not hardcode `@e...` refs in documentation or scripts. They change after
  navigation and after many UI updates.
- Use `agent-browser snapshot -i` before each step that needs an element ref,
  then click or fill the ref that corresponds to the visible label on the page.
- Do not combine `snapshot` with later ref-based actions in the same command
  chain if those refs were selected before the snapshot ran.
- For account selection in the Accounts picker, prefer `scrollintoview @rowRef`
  followed by `check @checkboxRef`, both taken from the same open-picker
  snapshot.
- Verify the report heading and the date fields after updating, rather than
  assuming the change applied.

### Example

To inspect transactions on 2 Dec 2024:

```bash
agent-browser snapshot -i
# click the "Reporting" button from the top nav

agent-browser wait 3000
agent-browser snapshot -i
# click the "Account Transactions" report link

agent-browser wait 3000
agent-browser snapshot -i
# click the "Grouping/Summarising" button

agent-browser wait 1000
agent-browser snapshot -i
# select the "None" option from the grouping chooser

agent-browser wait 500
agent-browser snapshot -i
# optionally open the accounts dropdown and restrict the report to specific accounts
# optionally open the "Columns" menu and enable "Account", "Account Code",
# and "Account Type"

agent-browser wait 3000
agent-browser snapshot -i
# fill the start date field with "2 Dec 2024"
# fill the end date field with "2 Dec 2024"
# click the "Update" button

agent-browser wait 3000
agent-browser snapshot -i
```

Always re-snapshot after opening the report, after changing grouping, after
changing `Accounts to include` if you use it, and after updating the date
range, because the refs change.

## Appendix: Filtered Account Search Fallback

This is an alternative account-picking approach. It works, but it is slower
than the full-list `scrollintoview` workflow above. Use it as a fallback if the
full-list method becomes unreliable on a specific page state.

### Workflow

1. Open the Accounts picker.
2. Reset the hidden selection state first by clicking `Select all` and then `Deselect all`.
3. Type one account code into the search box, for example `1110`.
4. Take a fresh snapshot.
5. Check the single visible checkbox for that filtered result.
6. Repeat steps 3 to 5 for each additional account.
7. Confirm the final selected-account count.
8. Close the picker.

### Notes

- The Accounts picker only changes which options are visible when filtered. It does not reset the underlying selected-account set.
- If you filter first and then toggle selection, you can leave many hidden accounts selected and get misleading report output.
- The one-account-at-a-time filtered method works reliably, but it is slower than selecting directly from the full list.

## Viewport

Xero's dense pages benefit from fitting the browser before automation. Follow
the `agent-browser-local` viewport guidance, which delegates to the standalone
`agent-browser-viewport` helper.

## Non-standard UI Elements

Xero uses non-standard HTML for many interactive elements.

### Options menus

Xero payment and transaction pages use the generic `dl`/`dt`/`dd` pattern
documented in `agent-browser-local`. Their generated ids vary, so locate the
menu by its visible `Options` label.

Common `onclick` patterns seen on payment/transaction pages:

- `showUnrecWarning` or `singleUnrecWarning` — Unreconcile (varies by page type)
- `DeleteTransaction` — Remove & Redo
- `PrintPopup` — View Receipt (PDF)

On **Manual Journal** pages the dropdown is labelled "Journal Options" (not "Options"):

```bash
# Force open and inspect
agent-browser eval --stdin <<'EVALEOF'
const joDl = Array.from(document.querySelectorAll('dl')).find(el => el.innerText.trim().startsWith('Journal Options'));
const joDd = joDl.querySelector('dd');
joDd.style.display = 'block';
joDd.style.visibility = 'visible';
joDd.style.opacity = '1';
joDd.innerHTML
EVALEOF

# Click Edit on a posted manual journal
agent-browser eval "document.querySelector('dd a[href*=\"edit=true\"][href*=\"invoiceID\"]').click()"
```

**Editing posted manual journals:** Xero allows editing line descriptions (and other fields)
on posted manual journals via Journal Options → Edit. The edit page works the same as the
draft edit page — click the empty cell to the left of the description cell to activate the
textbox, fill it, then click Post.

The journal UUID remains unchanged after editing. The sequential journal number (e.g. #11791)
increments to a new number (e.g. #11793) as a display artefact, but the old number no longer
exists — Xero edits in place. There are no duplicates or voided entries created.

**CRITICAL: Never refer to a manual journal by its sequential `#NNNNN` number
in notes, todos, commit messages, or any persisted artefact.** That number is
unstable — every edit-in-place renumbers it, so a doc that says "#11799" today
points at nothing tomorrow.

**The durable identifier is the full UUID** (e.g.
`deadbeef-0000-4000-8000-000000000000`). Every persisted reference to a manual
journal must include either the full UUID or — preferably — the full
click-through URL `https://go.xero.com/Journal/View.aspx?invoiceID=<full-uuid>`,
because you cannot reconstruct the URL without the full UUID anyway.

The **truncated UUID prefix** (first segment, e.g. `deadbeef`) is purely a
convenient shorthand for repeated mentions of the same journal within a
discussion — to avoid repeating the long form once it has been introduced. It
is not a substitute for the full UUID/URL: the durable record must always
contain the full form somewhere nearby (typically the first time the journal
is mentioned). The sequential `#NNNNN` is acceptable as transient context
inside a single conversation, but never write it down anywhere durable.

**This applies to CHAT with the user too, not only persisted artefacts.** When
you name a journal (or any transaction) in a message to the user, its FIRST
mention must carry **date/timestamp + a human-readable description of what it
does (DR/CR + amount + purpose) + the click-through URL** — never a bare
`#NNNNN` or bare UUID on its own. The user cannot resolve opaque IDs and is
left "flying blind" by them. This holds for Cryptio transactions and on-chain
hashes as well (give the Cryptio both-params link / block-explorer URL +
timestamp + what it is). Only after the full, described form has been given
once may a short prefix be used for repeat mentions in the same message thread.

### ExtJS autocomplete dropdowns

Xero account and tax-rate fields use the ExtJS combo pattern documented in
`agent-browser-local`. On manual journals, activate the empty account cell,
`type` the account code, select the exact `.x-combo-list-item`, and verify that
the cell displays the chosen account.

## Bank Reconciliation — Find & Match

### General flow

1. Click "Find & Match" on the statement line
2. Re-snapshot to get fresh refs within the opened panel
3. If the invoice is in a foreign currency, uncheck "Show GBP items only" (see below)
4. The results list will show available invoices/bills — tick the correct one
5. Confirm totals match in section 3 before reconciling
6. Click Reconcile — **only with explicit user permission**

**CRITICAL: Never reconcile without explicit user permission for each individual line.**

**CRITICAL: Always match against an invoice/bill in the results
list. NEVER create a payment transaction — that double-counts the
income.**

### "Show GBP items only" checkbox

The checkbox ref from snapshot may not toggle correctly. If so, use JS
instead:

```bash
agent-browser eval "document.getElementById('showBankCurrencyToggle').click()"
agent-browser eval "document.getElementById('showBankCurrencyToggle').checked"  # verify
```

### Partial payments (Split)

When the bank line covers only part of an invoice:

1. Tick the invoice in the results list — a "Split" link appears next to it
2. **For foreign currency invoices: click the "Rate from DD Mon YYYY" button first** to load
   the correct exchange rate. This shows a tooltip (from XE.com) with the rate, e.g.
   "1 GBP = 1.35415 USD". Take a screenshot to read it — it does not appear in snapshots.
   Note: section 3 may show a different (wrong) rate outside the tooltip — ignore that,
   the XE.com tooltip is always correct.
3. Calculate the part payment amount in the invoice's currency:
   `GBP amount × XE.com rate` (e.g. £898.05 × 1.35415 = $1,216.34)
4. Click "Split" — a dialog appears with Balance, Part payment, and Remaining amount
5. Enter the calculated amount, then click Split — the link changes to "Unsplit" confirming success
6. Verify section 3 shows "Totals match" before proceeding

### Ticking/unticking invoices in the results list

Use `agent-browser check @eN` to tick an invoice. To untick, use `agent-browser click @eN`
— do not use `check` to untick, as it may re-tick instead.

After ticking/unticking, verify the correct invoice appears in section 2 before proceeding.

### Verifying input field values

`agent-browser get text @eN` does not work for input field values. Use a screenshot instead.
