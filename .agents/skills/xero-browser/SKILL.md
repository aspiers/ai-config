---
name: xero-browser
description: General Xero browser automation notes. Use when automating any Xero page with agent-browser — covers non-standard UI patterns, waiting, and dropdown menus.
---

# Xero Browser Automation

General notes for automating Xero with `agent-browser`.

For Xero MCP server usage (OAuth, list-* tools, searching records by ID
vs. pagination), see the separate [`xero-mcp`](../xero-mcp/SKILL.md)
skill instead.

## Fiduciary Responsibility

This is accounting with fiduciary responsibility. **Always stop and report
any discrepancy** — in amounts, dates, accounts, or anything that doesn't
match expectations — rather than assuming it is "likely fine".
Do not proceed past a discrepancy — surface it to the user immediately.

**CRITICAL: Never delete anything in Xero without explicit user permission.**
This includes invoices, bills, payments, bank transactions, contacts,
manual journals, attachments, reconciliations, and any other record or
artifact. If deletion seems like the cleanest fix, stop and ask first.

## Waiting

**Never use** `agent-browser wait --load networkidle` — Xero never reaches networkidle.
Use `agent-browser wait 3000` instead.

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

The default viewport (1280x720) is too short for many Xero pages, causing
elements to overlap or scroll unexpectedly. Use this before starting Xero
automation:

```bash
agent-browser set viewport 1900 900
```

This takes effect immediately on the current session — no reload needed.

## Non-standard UI Elements

Xero uses non-standard HTML for many interactive elements.

### Dropdown menus (`dl`/`dt`/`dd` pattern)

Xero renders dropdown menus as `<dl>` elements (e.g. Options menus on payment/transaction pages).
The `<dt>` is the visible trigger; the `<dd>` contains the `<ul>` of items.

**IMPORTANT: The `dl` element ID varies by page** (e.g. `ext-gen18`, `paymentOptions`, etc.).
Never hardcode the ID.

**Preferred approach: snapshot first, click the ref.**

```bash
agent-browser snapshot -i
# Look for a ref matching the Options dt or the menu items, then click it directly.
agent-browser click @eN
```

**Fallback (if snapshot refs don't work): find by text, force the `dd` visible, click via JS.**

CSS hover/class toggling can make the `dd` invisible — in that case force it open:

```bash
# 1. Force open the dd and inspect available actions
agent-browser eval --stdin <<'EVALEOF'
const dl = Array.from(document.querySelectorAll('dl')).find(el => el.innerText.trim().startsWith('Options'));
const dd = dl.querySelector('dd');
dd.style.display = 'block';
dd.style.visibility = 'visible';
dd.style.opacity = '1';
dd.innerHTML
EVALEOF

# 2. Click the desired item by matching its onclick attribute
agent-browser eval --stdin <<'EVALEOF'
const dl = Array.from(document.querySelectorAll('dl')).find(el => el.innerText.trim().startsWith('Options'));
dl.querySelector('dd a[onclick*="FUNCTION_NAME"]').click()
EVALEOF
```

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

### ExtJS autocomplete dropdowns (general)

Xero uses ExtJS for many autocomplete/combo dropdowns throughout the application,
not just the account field on manual journals. The pattern below applies generally.

Examples include the account field on manual journals, tax rate fields, and
other combo fields throughout Xero. The dropdown is **not visible in snapshots** (neither `-i`,
`-i -C`, nor plain `snapshot`) as a clickable ref — it appears only as a bare
`StaticText` at the bottom of the full snapshot with no ref assigned.

`agent-browser find text "..." click` does NOT work — it clicks the text node
itself, not the containing element that has the click handler.

**Correct approach:**

1. Snapshot `-i` to get the account cell ref (it will be an empty cell after the description cell)
2. Click the account cell to activate the textbox
3. Snapshot `-i` again to confirm the textbox ref (e.g. e58)
4. `agent-browser type @eN "6999"` — use `type` not `fill`
5. Wait 800ms for the dropdown to appear
6. Click the item via JS targeting `.x-combo-list-item` by text:

```bash
agent-browser eval "Array.from(document.querySelectorAll('.x-combo-list-item')).find(el => el.innerText.trim() === '6999 - Realised currency gains or losses').click()"
```

7. Snapshot `-i` to confirm the account cell now shows the account name

**Why JS and not `find text`?** The click handler is on the `.x-combo-list-item`
div, not the text node. `find text` clicks the text node which doesn't bubble
correctly. The JS approach finds the correct container element by text and
calls `.click()` on it directly.

**Note on refs between snapshots:** Ref IDs (e.g. `@e58`) can be
reassigned every time the page updates. So to be safe, always
re-snapshot before using a ref — never reuse refs from a previous
snapshot.

### Confirmation dialogs

After triggering an action that produces a confirmation dialog, use `agent-browser snapshot -i`
to get fresh refs, then click the relevant ref directly. Do not assume element types or use
text-based selectors.

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
