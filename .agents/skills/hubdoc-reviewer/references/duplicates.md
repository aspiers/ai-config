# Duplicates handling

How to detect and resolve potential-duplicate documents in Hubdoc before
publishing.

## Detection

**Warning banner (Review tab)**: A yellow "Potential Duplicate Document"
banner with a "Show Duplicates" button appears at the top of the editor
when Hubdoc has detected potential matches.

- The `"Duplicate Documents"` heading is **always** present in the DOM
  (hidden) — do not use its presence as an indicator. Only act when the
  warning banner and "Show Duplicates" button are actually visible.
- If visible, click "Show Duplicates" and investigate **before doing
  anything else** on this document.

**No warning (search box)**: When using the Hubdoc search box rather than
browsing the Review tab, duplicates do **not** show a banner — they just
appear as multiple items in the left panel with the same
supplier/date/amount. Always inspect the left panel for multiple entries
from the same supplier before proceeding.

## Investigating the duplicates

Click "Show Duplicates" to open the duplicate-documents drawer. For each
duplicate shown, note:

- Supplier, date, amount, due date
- Status icon (green tick = archived/published, warning triangle = unpublished/Review)
- Doc ID (from `data-dup-docid` on the `.duplicate-list-item`)

You can read the duplicate list programmatically:

```bash
agent-browser eval --stdin <<'EOF'
(function() {
  return JSON.stringify(Array.from(document.querySelectorAll('.duplicate-list-item')).map(function(item) {
    const stateIcon = item.querySelector('.workflow-state-icon');
    return {
      docId: item.getAttribute('data-dup-docid'),
      text: item.innerText,
      state: stateIcon ? stateIcon.className : null,
    };
  }), null, 2);
})()
EOF
```

`workflow-state-archived` = published (green tick). `workflow-state-review`
= still in Review (warning triangle).

## Presenting to the user

Present the full details using a table like this example:

| # | Doc ID    | Type                 | Invoice #                         | Date         | Amount     | Due Date     | Status                  |
|---|-----------|----------------------|-----------------------------------|--------------|------------|--------------|-------------------------|
| 1 | 867916854 | **Receipt** (paid)   | HMXGZYIU-0001, Receipt# 2261-7480 | Jan 28, 2026 | $21.23 USD | —            | ⚠ unpublished (current) |
| 2 | 867916848 | **Invoice** (unpaid) | HMXGZYIU-0001                     | Jan 28, 2026 | $21.23 USD | Jan 28, 2026 | ✓ published             |

Heuristics for identifying type when not labelled:

- "Receipt" header on PDF, no due date, often shows "Paid on …" → Receipt
- "Invoice" header on PDF, has due date → Invoice

## Decision rules

- Receipts are preferred over invoices because they include proof of payment.
- **Both unpublished**: keep the receipt, trash the invoice.
- **One published, one unpublished**: trash the unpublished one — but
  **wait for explicit user confirmation before doing so**.
- **Exception**: if the already-published one is an invoice and the
  unpublished one is a receipt, it is not worth switching — just trash the
  unpublished receipt.

Only proceed with reviewing/publishing the current document once
duplicates are resolved.

## Trashing a document

### From within the duplicates drawer (preferred)

Each `.duplicate-list-item` in the drawer has a `button.move-to-trash`.
Clicking it trashes that specific doc **silently** — there is no
confirmation dialog. Target by `data-dup-docid`:

```bash
agent-browser eval --stdin <<'EOF'
(function() {
  const docId = '903642305';
  const item = document.querySelector('.duplicate-list-item[data-dup-docid="' + docId + '"]');
  if (!item) return 'no item';
  item.querySelector('button.move-to-trash').click();
  return 'trashed ' + docId;
})()
EOF
```

**Caveat — stale list cache**: After Move-To-Trash, the Review tab's
left-panel doc list may still show the trashed document. The main pane
also stays on its old fields. Switching to another tab (e.g. Processing)
and back to Review refreshes the list. A full `F5` reload does **not**
reliably refresh it on its own — tab-switch is more reliable.

### From the main editor (top-right Delete link)

Use this when you want to trash the *currently-open* doc, not a duplicate
in the drawer. It has class `delete-btn action`:

```bash
agent-browser eval --stdin <<'EOF'
document.querySelector('a.delete-btn.action')?.click();
EOF
```

A confirmation dialog appears. Use `snapshot -i` to find the OK ref — it
appears as `link "OK"` (not a `<button>`), then click it:

```bash
agent-browser snapshot -i
agent-browser click @eN  # where @eN is the "OK" link ref
```

## Closing the duplicates drawer

After resolving duplicates, **close the duplicates drawer** before
navigating to the next document. The drawer overlays the doc list and
prevents the main pane from updating when you click another doc — even
if the click registers, the heading/fields stay stuck on the previous
document.

The close button is `#close-drawer` (an `<i class="fas fa-times">`
element):

```bash
agent-browser eval --stdin <<'EOF'
document.getElementById('close-drawer').click();
EOF
```
