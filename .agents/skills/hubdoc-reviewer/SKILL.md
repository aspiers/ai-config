---
name: hubdoc-reviewer
description: Review all unreviewed documents in Hubdoc. Use when reviewing, processing or publishing Hubdoc receipts and bills.
---

# Hubdoc Reviewer

Reviews all documents in the Hubdoc Review tab, one by one.

## Skill maintenance goal

When adding or updating instructions in this skill, all documented methods
(JS selectors, click sequences, field-setting approaches) **must be tested
and verified to work** before being committed to the skill. Never document
untested code. The goal is to build bulletproof, reliable documentation so
that Hubdoc automation works first time without painful trial and error.

## Prerequisites

- The `agent-browser` skill is installed
- `agent-browser` connected to Chrome
- Tab open on https://app.hubdoc.com (open new one if necessary)

**Do not use** `agent-browser wait --load networkidle` — Xero never
reaches `networkidle`; use `agent-browser wait 3000` instead.

## Logging in

Always use "Sign In With Xero" — never use the email/password form:

```bash
# If the login page appears, click "Sign In With Xero"
agent-browser snapshot -i  # find the Sign In With Xero link
agent-browser click @eN
agent-browser wait 3000
```

## Finding and interacting with page elements

**Always use `snapshot -i -C`** (not just `-i`) when looking for interactive
elements. The `-C` flag includes cursor-interactive elements (divs with
onclick, cursor:pointer) which many Hubdoc buttons and controls rely on.
Omitting `-C` will cause buttons to be invisible to the snapshot.

Choose the approach based on the nature of the element you're looking for:

- **Element with a known ID** (see Field IDs table below) → JS eval to confirm
  which ref corresponds to that ID. Use JS only to *identify*, not to set values.
- **Labelled interactive element** (button, link, named input) →
  `snapshot -i -C`; use the ref directly.
- **Element identified by surrounding label text** (e.g. an unlabelled combobox
  next to an "Account Code" label) → `snapshot` (no `-i`) to get the full
  accessibility tree including non-interactive text, then find the label and
  identify the adjacent ref.
- **Nothing else works** → screenshot as a last resort for visual confirmation.

Taking into account some exceptions listed below, as a general rule
once the correct ref is identified, first try to interact via

    agent-browser select/fill/click @eN

and similar, and only move onto other techniques like `eval` with JS
if that fails.

## Xero vs Xero Files

Hubdoc has a **Xero** destination section and a separate **Xero Files**
section. They are not interchangeable.

- For accounting publish configuration, always use the **Xero** section.
- **Never use the Xero Files section** when configuring or publishing a
  document for accounting.
- If publish fields are not visible, expand the **Xero** section itself,
  not the Xero Files section.
- When inspecting the DOM, verify you are using `xero-edit-integration`
  or `push-to-xero-*` fields, not `xerofiles-edit-integration` or
  `push-to-xerofiles-*` fields.
- **Scroll the Xero section into view before interacting with it.** Its
  controls (Status, Account Code, Contact, Publish button) sit below the
  fold on most viewports, and clicks on off-screen refs can miss or hit
  the wrong element. Use `agent-browser scrollintoview @ref` on the Xero
  section header (or any ref inside it) before snapshotting and acting:
  ```bash
  agent-browser snapshot -i -C            # find the Xero section ref
  agent-browser scrollintoview @eN        # scroll Xero section into view
  agent-browser snapshot -i -C            # re-snapshot for in-view refs
  ```
  Do NOT use `eval` with `scrollIntoView()` — prefer the native
  `agent-browser scrollintoview` command (same convention as
  `xero-browser` skill).

## Account code guidance

Before guessing an account code, consult the local accounting guidance
for your workspace — typically a file under your project's notes
directory, an environment variable like `$ACCOUNTING_NOTES`, or a
project-level CLAUDE.md / AGENTS.md entry. Account-code conventions
vary per Xero organisation, so never rely on memorised codes from
another tenant.

## Field IDs

All TRANSACTION DETAILS fields are manipulated by ID — do NOT use
`agent-browser fill` with snapshot refs for these fields, as the unlabelled
textboxes are display-only shims and will corrupt other fields (e.g. Supplier).
Always use the JS approach below.

| Field            | Element ID              | Notes                        |
|------------------|-------------------------|------------------------------|
| Document Type    | `editor-document-type`  | `<select>`                   |
| Supplier         | `editor-vendor-id`      | `<select>`                   |
| Invoice / Ref. # | `editor-invoice-number` | `<input type="text">`        |
| Date             | `editor-bill-date`      | `<input type="text">`        |
| Total Amount     | `editor-amount`         | `<input type="text">`        |
| Currency         | `editor-currency`       | `<select>`                   |
| Tax Rate         | `editor-taxrate`        | `<select>` value `NONE` = 0% |

## Setting field values via JS

For `<input>` fields:
```bash
agent-browser eval --stdin <<'EVALEOF'
const el = document.getElementById('editor-invoice-number');
el.value = '2397-5919';
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
el.value
EVALEOF
```

For `<select>` fields (Document Type, Currency, Tax Rate):
```bash
agent-browser eval --stdin <<'EVALEOF'
const sel = document.getElementById('editor-document-type');
sel.value = 'Receipt';  // must match exact option value
['change', 'input'].forEach(ev => sel.dispatchEvent(new Event(ev, {bubbles: true})));
sel.value
EVALEOF
```

Document Type option values: `Invoice`, `Receipt`, `Statement`, `Report`,
`CSV`, `Check`, `Deposit`, `eTransfer`, `Invoice (AR)`, `Payment`,
`Credit Memo`, `Purchase Order`, `Other`.

## Uploading documents

To upload a PDF or image to Hubdoc:

1. Click the "Upload Document" button
2. In the upload modal, set the file on the hidden file input:
   ```bash
   agent-browser upload "#upload-modal input[type='file']:not(#file-upload)" /path/to/file.pdf
   agent-browser wait 5000
   ```
3. Verify the upload completed by checking the document list for the new entry
4. **Close the upload modal** — it does not close automatically. Click the
   X button (link "X" ref) or the close button to dismiss it. If the modal
   is left open it will interfere with subsequent interactions.

## Downloading and reading Hubdoc PDFs

When the on-page preview is not enough to determine exact travel routes,
dates, invoice numbers, or other receipt details, download the original
document and read the PDF directly.

Workflow:

1. Open the document in the normal Hubdoc UI.
2. Use `snapshot -i -C` and identify the `Download` link/button from the
   document action bar.
3. Prefer downloading to an explicit absolute path under the repository's
   `tmp/` directory.
4. Use the **working sequence** below:

```bash
agent-browser click @eN
agent-browser wait --download "$PWD/tmp/document.pdf"
```

Do **not** assume `agent-browser download @eN /path` will always yield a
readable flat file in Hubdoc. The verified reliable method for Hubdoc is the
click-plus-wait flow above.

5. **Immediately verify the artifact on disk.** Do not assume the success
   message means the file is readable at the requested path.
6. Inspect the saved path. In Hubdoc, the download may appear as a wrapper
   directory at the requested path containing the actual downloaded file.
7. Be aware that Hubdoc download behavior is inconsistent across documents:
   some downloads materialize as the wrapper directory above, while others
   report success but do not appear at the requested path. If that happens,
   stop assuming the download worked and fall back to the on-page screenshot /
   visible text for the current task unless the PDF is essential.
8. Read the resulting PDF content from the downloaded artifact when the file
   is actually present.

Do this instead of guessing route/date details from partial preview text.

## Searching for documents

To search for a specific document, click the search icon (magnifying glass
button, typically `@e2` after initial snapshot) to open the advanced search
panel. This reveals several fields:

- **Has the Words** (`@e6` or similar) — free text search across document content
- **Date range** — From/Through date fields
- **Supplier** — filter by supplier name
- **Document type** — filter by type

```bash
# Open the advanced search panel
agent-browser snapshot -i
agent-browser click @e2              # click the search/magnifying glass button
agent-browser wait 1000
agent-browser snapshot -i            # get refs for search fields

# Fill "Has the Words" and submit by pressing Enter
agent-browser fill @e6 "search term"
agent-browser press @e6 Enter        # submit search (no Search button exists)
agent-browser wait 3000
```

The ref numbers may vary — use `snapshot -i` after opening the search panel
to identify the correct ref for the "Has the Words" field.

**There is no longer a Search button to click** — submit the query by
pressing `Enter` in the search textbox via `agent-browser press @ref Enter`.

If no results appear in the document list, the document is not in Hubdoc.

## Process

### 1. Navigate to Hubdoc and open the Review tab

**IMPORTANT — check existing tabs first**: Before opening a new Hubdoc tab,
check if one is already open. Opening a second tab to the same site can cause
the browser to hang or lose focus on the original tab.

```bash
# 1. List all open tabs
agent-browser tab list

# 2. If a Hubdoc tab exists, switch to it by its tab number
agent-browser tab 0    # switch to tab 0 (or whichever has Hubdoc)

# 3. Only open a new tab if no Hubdoc tab exists
agent-browser open https://app.hubdoc.com
agent-browser wait 3000
```

**IMPORTANT — switching tabs**: Do NOT use JS `.click()` on tab elements and do
NOT use `agent-browser eval` to click tabs. Doing so corrupts the tab state and
empties the document list. The only correct approach is `agent-browser click @ref`
using the ref from `agent-browser snapshot -i -C`:

```bash
agent-browser snapshot -i -C  # find e.g. clickable "Review" [ref=e26]
agent-browser click @e26
agent-browser wait 2000
agent-browser screenshot
```

**NOTE — documents still processing**: Documents that are still being processed
by Hubdoc's OCR pipeline only appear in the **All** and **Processing** tabs —
they will NOT appear in the **Review** tab yet. If you are told to work on
specific documents that cannot be found in Review, check the **All** tab and
click the document directly from there.

### 2. Check how many documents need review

```bash
agent-browser snapshot -i -C
```

The left panel lists all documents awaiting review. Work through them top to bottom.
Use a screenshot only if you need to see thumbnails or can't identify documents from the snapshot text.

### 2b. Check for duplicate warning

**IMPORTANT**: Never use `window.open()` or `window.location.href` to navigate to
document URLs — both will open/navigate to the raw PDF, losing the Hubdoc review UI.
Always navigate by clicking document items in the left panel, or by using
`agent-browser open https://app.hubdoc.com` and then clicking through the UI.
Opening a new tab also shifts `agent-browser` focus away from the review page.
All investigation must be done within the current tab.

**Navigating between documents in the left panel**: Document list items are `<a>`
elements with no `href` — they use click handlers. Find them via:

```bash
agent-browser eval --stdin <<'EVALEOF'
const items = document.querySelectorAll('span.biller-name');
// Click the Nth document (0-indexed):
items[1]?.closest('a')?.click();
EVALEOF
```

**Duplicates when searching**: When using the Hubdoc search box rather than
browsing the Review tab, duplicates do NOT show a warning banner — they simply
appear as multiple items in the left panel with the same supplier/date/amount.
Always inspect the left panel for multiple entries from the same supplier before
proceeding.

Before reading fields, check if there is a "Potential Duplicate Document" warning banner
with a "Show Duplicates" button visible. The "Duplicate Documents" heading is always
present in the DOM (hidden) — do **not** use its presence as an indicator. Only act
if the warning banner and "Show Duplicates" button are actually visible.
If so, click "Show Duplicates" and investigate **before doing anything else**.

For each duplicate shown:

- Note the supplier, date, amount, due date, and status icon (green
  tick = archived, warning = unpublished)

- Present the full details to the user and ask them to review, using a
  table like this example:

  | # | Doc ID    | Type                 | Invoice #                         | Date         | Amount     | Due Date     | Status                  |
  |---|-----------|----------------------|-----------------------------------|--------------|------------|--------------|-------------------------|
  | 1 | 867916854 | **Receipt** (paid)   | HMKGXYIU-0001, Receipt# 2661-7468 | Jan 28, 2026 | $21.23 USD | —            | ⚠ unpublished (current) |
  | 2 | 867916848 | **Invoice** (unpaid) | HMKGXYIU-0001                     | Jan 28, 2026 | $21.23 USD | Jan 28, 2026 | ✓ published             |

- In general, receipts are preferred over invoices as they include
  proof of payment.  If both are unpublished, suggest keeping the
  receipt and trashing the invoice.

- If one duplicate is already published and the other is not, suggest
  moving the unpublished one(s) to trash — but **wait for explicit
  user confirmation before doing so**.  Exception: if the
  already-published one is an invoice and the unpublished one is a
  receipt, it is not worth switching — just trash the receipt.

- Only proceed with reviewing/publishing the current document once
  duplicates are resolved

#### Trashing a document

Click the Delete button via JS (it has class `delete-btn action`):

```bash
agent-browser eval --stdin <<'EVALEOF'
document.querySelector('a.delete-btn.action')?.click();
EVALEOF
```

A confirmation dialog appears. Use `snapshot -i` to find the OK ref — it
appears as `link "OK"` (not a `<button>`), then click it:

```bash
agent-browser snapshot -i
agent-browser click @eN  # where @eN is the "OK" link ref
```

### 3. For each document

Use `agent-browser snapshot` for checking UI state and navigation —
it's faster and gives structured data. Only use `agent-browser
screenshot` when you need to read the actual document content (the
inline PDF). In particular:

- **Use snapshot first** to check field values, button states, and UI
  structure — it's faster and cheaper than a screenshot.
- **Use screenshot only** when you need to read the rendered PDF content
  (invoice number, date, amount, etc.) that isn't exposed in the
  accessibility tree.

Take a screenshot to read the document — it renders inline in the
Hubdoc review UI so you can read it directly without opening the PDF
separately.  Then read and verify all current field values via JS
before making any changes:

```bash
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify({
  docType:   document.getElementById('editor-document-type')?.value,
  supplier:  document.getElementById('editor-vendor-id')?.value,
  invoiceNum: document.getElementById('editor-invoice-number')?.value,
  date:      document.getElementById('editor-bill-date')?.value,
  amount:    document.getElementById('editor-amount')?.value,
  currency:  document.getElementById('editor-currency')?.value,
  taxRate:   document.getElementById('editor-taxrate')?.value,
}, null, 2)
EVALEOF
```

**IMPORTANT — field reset behaviour**: Certain actions reset all transaction
detail fields (Document Type, Invoice#, Date, Amount, Tax Rate):

- Clicking **Create** to create a new Hubdoc supplier resets all fields
- Clicking **Create** to create a new Xero contact resets all fields

Therefore the correct order is:

1. Create new supplier (if needed) and click Create
2. Set up Xero destinations (expand, search/create contact, set Status and Account Code)
3. Click Create for new Xero contact (if needed)
4. **Only then** fill in all transaction detail fields (Invoice#, Date, Amount, Tax Rate)

This ensures nothing gets wiped before publishing.

**IMPORTANT — field interaction**: Do NOT use JS eval to set the Date or
Amount fields — Hubdoc's form validation will reject them and show "This field
is required" on publish even if the value appears correct. Use native browser
interaction instead:

- **Date**: Click the date field ref to open the calendar picker. The
  calendar header shows `«` (back), month/year, `»` (forward). Navigate
  to the correct month using `«`/`»`, then click the day cell. Tested
  method:
  ```bash
  agent-browser click @eDateField              # opens calendar
  agent-browser wait 500
  agent-browser snapshot -i -C -s "table"      # find « » and day cells
  agent-browser click @eBackArrow              # navigate months as needed
  agent-browser wait 500
  agent-browser snapshot -i -C -s "table"      # re-snapshot for new month
  agent-browser click @eDayCell                # click the correct day
  ```
  Verify with: `agent-browser eval 'document.getElementById("editor-bill-date")?.value'`
  Do NOT use `fill`, `type`, or JS eval for the date field — they appear
  to succeed but the value reverts or gets set to today's date.
- **Amount**: Use `agent-browser fill @eN "143.89"` (tested, works).
  Verify with: `agent-browser eval 'document.getElementById("editor-amount")?.value'`
  Also verify currency wasn't corrupted:
  `agent-browser eval 'document.getElementById("editor-currency")?.value'`
- **Invoice / Ref. #**, **Tax Rate**, **Document Type**, **Supplier**: JS eval
  is fine for these as they don't have the same validation issue.

Then fill/correct each field:

#### Document Type

- If the document is a **receipt**, or an **invoice marked as paid** → set to **Receipt**
- If the document is an **invoice** (unpaid or unknown status) → set to **Invoice**
- Any other case → **stop and ask the user** what type it should be

#### Mark as Paid

- If Document Type is **Receipt**, tick the **Mark as Paid** checkbox
  (`#paid-status-checkbox`) if it is not already checked:

  ```bash
  agent-browser eval --stdin <<'EVALEOF'
  const cb = document.getElementById('paid-status-checkbox');
  if (!cb.checked) cb.click();
  cb.checked
  EVALEOF
  ```

#### Invoice / Ref. #

- If the field is empty, or contains a Hubdoc-generated number prefixed with `HD-`,
  read the reference/invoice number from the attached document and enter it.

#### Currency

- Verify it matches the attached document (e.g. `USD` if the doc is in US$).

#### Date

- Verify it matches the attached document.

#### Total Amount

- Verify it matches the attached document.

#### Tax Rate

- Always set to `NONE` (No VAT 0%). Verify it is already `NONE`; set it if not.

#### Xero Contact

- In the Destinations section, the **Contact** field must be set to a matching
  Xero contact. Search by name, omitting generic suffixes like "Corporation",
  "Inc", "Ltd", etc. (e.g. search "Railway" not "Railway Corporation").
- After typing in the search box, a dropdown appears. Use `snapshot -i` to get
  the listbox option ref, then `agent-browser click @eN` to select it. Do NOT
  rely on JS `.click()` on the `<li>` — it does not reliably trigger selection.
- If no matching contact is found, **stop and ask the user** what contact name
  should be created before proceeding.
- When creating a new contact: select the "+ Add '...' as a new contact"
  option from the dropdown. This populates a "New Contact" text field.
  You **must then click the "Create" button** to actually create the contact
  in Xero. The contact is not created until the button is clicked.
  **The Create button requires `snapshot -i -C`** to be found — it is a
  cursor-interactive element that `snapshot -i` alone will not pick up.
  If you cannot find a button you expect to exist, **always try
  `snapshot -i -C` before resorting to JS or other workarounds**.
  Also note there may be TWO Create buttons on the page: one for the
  Hubdoc supplier (class `create-vendor`) and one for the Xero contact.
  Make sure you click the correct one — the Xero contact Create button
  appears below the "New Contact:" text field in the Xero destination
  section. Never use `find text "Create" click` as it may click the
  wrong one.
  **Always verify creation succeeded** by re-snapshotting and checking that
  the contact combobox shows "× ContactName" without a red "This field is
  required" validation error. If the error persists, the contact was not
  properly linked — clear the field (click the × next to the contact name)
  and re-select from the dropdown.
- **Clearing the contact field**: The × button to clear a selected contact
  is a `<span class="select2-selection__choice__remove">`. Do NOT use
  `find text "×" click` as this is dangerously unscoped and could click
  any × on the page. Instead, use this tested JS:
  ```bash
  agent-browser eval --stdin <<'EVALEOF'
  document.querySelector('span.select2-selection__choice__remove')?.click();
  EVALEOF
  ```
  After clearing, **verify it actually cleared** by checking the remove
  button no longer exists:
  ```bash
  agent-browser eval --stdin <<'EVALEOF'
  (function() {
    var choice = document.querySelector('span.select2-selection__choice__remove');
    return JSON.stringify({ cleared: !choice });
  })()
  EVALEOF
  ```
  If `cleared` is `false`, the click didn't work — retry or investigate.
  Only proceed once confirmed cleared, then search and select the correct
  contact.

#### Xero Status

- Always set **Status** to **Awaiting Payment** (value `authorised`). This applies
  to both receipts and invoices.
  - The select ID is dynamic per document (e.g. `push-to-xero-<docid>-status`)
  - Use the general approach above to identify the ref, then
    `agent-browser select @eN "authorised"`.
  - If refs are still unlabelled after all steps, fall back to JS:
    ```bash
    agent-browser eval --stdin <<'EVALEOF'
    const sel = Array.from(document.querySelectorAll('select'))
      .find(s => s.id.includes('-status'));
    sel.value = 'authorised';
    ['change','input'].forEach(ev => sel.dispatchEvent(new Event(ev, {bubbles:true})));
    sel.value
    EVALEOF
    ```

#### Supplier / Contact (Hubdoc)

- Verify correct. Do not change unless wrong.

#### Account Code

- Verify or set as appropriate.
- The Account Code combobox has no accessible name — use the general approach
  above to identify the correct ref, then `agent-browser select @eN "463"`.
- If that fails, use JS directly (the select ID follows the pattern
  `push-to-xero-<docid>-account-code`):

  ```bash
  agent-browser eval --stdin <<'EVALEOF'
  const sel = document.getElementById('push-to-xero-867916854-account-code');
  sel.value = '463';
  ['change','input'].forEach(ev => sel.dispatchEvent(new Event(ev, {bubbles:true})));
  sel.value
  EVALEOF
  ```

  Replace `867916854` with the actual document ID (visible in the select's ID
  when you inspect other Xero destination selects on the same page).

#### Description

- Verify or set as appropriate.

### 4. Ask the user for final review

**MANDATORY — never skip this step.** Before publishing, present a summary
table of all field values to the user (including what was changed vs. what was
already set) and wait for explicit confirmation before proceeding. Do not
publish speculatively.

**Always use the interactive questionnaire tool** (`mcp_question`) when you need
to ask the user multiple questions at once — for example when a document needs
guidance on supplier, currency, account code, or document type.

Example of the ideal summary format:

**Anthropic Receipt — Jan 26, 2026**

| Field            | Value                                                   |
| ---------------- | ------------------------------------------------------- |
| Document Type    | Receipt *(was: Choose — set)*                           |
| Mark as Paid     | ✓ checked *(was: unchecked — set)*                      |
| Supplier         | Anthropic                                               |
| Invoice / Ref. # | 2132-6089-6259 *(was: empty — set from receipt number)* |
| Date             | 26-01-2026                                              |
| Total Amount     | 86.53 GBP                                               |
| Tax Rate         | No VAT 0%                                               |
| Account Code     | 463 - IT Software and Consumables                       |
| Xero Status      | Awaiting Payment *(was: Draft — set)*                   |
| Xero Contact     | Anthropic *(already set)*                               |

### 5. Publish the document

Use `snapshot -i -C` to find the "Publish" button (not "Publish All") and
click it by ref. Do NOT use `button.publish-one-btn` as a CSS selector —
it may not match. Do NOT use `find text "Publish" click` as it may match
"Publish All" instead.

**NEVER click "Publish All".**

### 5b. Check for validation errors after publishing

After clicking Publish, wait and then check the publish status using JS:

```bash
agent-browser wait 3000
agent-browser eval --stdin <<'EVALEOF'
(function() {
  var failures = document.querySelectorAll('span.publish-state.publish-failure');
  if (failures.length > 0) {
    var alert = document.querySelector('div.failure-alert');
    var summarySpan = document.querySelector('span.publish-state.publish-failure');
    return JSON.stringify({
      status: 'error',
      message: alert ? alert.textContent.trim() : summarySpan.textContent.trim()
    });
  }
  var success = document.querySelector('span.publish-state.publish-success');
  if (success) {
    return JSON.stringify({ status: 'success' });
  }
  var notConfigured = document.querySelector('span.publish-state.publish-not_configured');
  if (notConfigured) {
    return JSON.stringify({ status: 'not_configured' });
  }
  return JSON.stringify({ status: 'unknown' });
})()
EVALEOF
```

- `status: "success"` → published successfully, proceed to next document
- `status: "error"` → publish failed. The `message` field contains the
  Xero validation error (e.g. period lock date issues). Report the error
  to the user and ask how to proceed.
- `status: "not_configured"` → Xero destination was not set up
- `status: "unknown"` → unexpected state, take a screenshot to investigate

### 6. Move to the next document

After publishing, click the **first document in the left panel** — this is the
safest way to advance, as it stays within the currently filtered tab:

```bash
agent-browser eval --stdin <<'EVALEOF'
document.querySelector('.document-list-item a, [class*="doc-list"] a')?.click();
EVALEOF
```

Or if that doesn't work, click by finding the first `<a>` ancestor of a
`span.biller-name` element:

```bash
agent-browser eval --stdin <<'EVALEOF'
document.querySelector('span.biller-name')?.closest('a')?.click();
EVALEOF
```

Or click the specific document link by href (as seen in the snapshot).

**Avoid using `span.next`** — while it exists and can be clicked, it navigates
within the full document list rather than the filtered tab, which can skip documents
or jump out of the Review/Failed tab. If ever needed:

```bash
agent-browser eval --stdin <<'EVALEOF'
document.querySelector('span.next')?.click();
EVALEOF
```

Note: `span.next` is a `<span>`, not an `<a>` or `<button>` — generic
button/link searches won't find it.

### 7. Repeat until the Review tab is empty

---

## Processing the Failed Tab

Once the Review tab is empty, click the **Failed** tab and process any documents there.
Use `agent-browser click @ref` (not JS eval) to switch tabs — see step 1 for details.

```bash
agent-browser snapshot -i -C  # find e.g. clickable "Failed" [ref=e25]
agent-browser click @e25
agent-browser wait 2000
agent-browser screenshot
```

### Why documents fail

Failed documents have previously attempted to publish to Xero but encountered a
validation error. The error is shown in the Xero destinations section (red
"Validation Err." message). Common causes:

- **Already published** — if the error says "This document cannot be **re**-published"
  and/or a "View Purchase in Xero" link is present, the document is already in Xero.
  Verify all fields are correct and move on — no further action needed.
- **Transient Xero sync failure** — the "Guid should contain 32 digits with 4
  dashes" error indicates a temporary failure; clicking Publish again is usually
  enough to fix it — but only after verifying all fields are correctly populated
- **Missing required fields** — Status, Publish As, Account Code, etc.

### Process for each failed document

The process is identical to the Review tab (steps 2b–6 above), with these
additional considerations:

1. Use `snapshot` to read the Xero error message in the Destinations section;
   take a screenshot only to read the rendered PDF content itself
2. Read the error shown in the Xero destinations section — this tells you what
   needs fixing
3. Fix all transaction detail fields as per the Review tab process
4. Pay particular attention to the **Xero-specific fields** in the Destinations
   section:
   - **Contact**: must match an existing Xero contact — search by name,
     omitting generic suffixes (see Xero Contact section above). If no match
     exists, stop and ask the user what contact to create.
   - **Status**: always **Awaiting Payment** (`authorised`) — see Xero Status section above
   - **Publish As**: typically "Purchase"
   - **Account Code**: verify or set as appropriate
5. Present a summary to the user and ask for confirmation before publishing
6. Publish using the same `button.publish-one-btn` approach

### Notes

- Failed documents may require more manual guidance than Review documents,
  as the failure reason varies
- If the error is unclear or you cannot resolve it, stop and ask the user
- After fixing and publishing, the document moves out of the Failed tab
- Repeat until the Failed tab is empty
