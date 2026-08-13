# Fields and JS interaction

**Use native `agent-browser` commands, targeting fields by CSS id selector.**
Verified 2026-08-13: `fill`, `type`, and `select` all work on these fields.

Do NOT use `agent-browser fill` with **snapshot refs** (`@eN`) — the unlabelled
textboxes are display-only shims and will corrupt other fields (e.g. Supplier).
The id selector (`#editor-amount`) is safe; the ref is not.

Do NOT reach for `eval` to set these fields. An earlier version of this file
said "always use the JS approach", which is wrong and caused a real failure —
see the JS-approval rule in the
[`agent-browser-local`](../../agent-browser-local/SKILL.md) skill.

```bash
agent-browser fill   "#editor-invoice-number" "2187780"
agent-browser select "#editor-taxrate" "NONE"
```

**`editor-amount` needs the full focus/type/blur sequence** — see "Total
Amount" below.

## Field IDs

| Field            | Element ID              | Notes                                   |
|------------------|-------------------------|-----------------------------------------|
| Document Type    | `editor-document-type`  | `<select>`                              |
| Supplier         | `editor-vendor-id`      | `<select>`                              |
| Invoice / Ref. # | `editor-invoice-number` | `<input type="text">`                   |
| Date             | `editor-bill-date`      | `<input type="text">` — **`DD-MM-YYYY`** |
| Total Amount     | `editor-amount`         | `<input type="text">`                   |
| Currency         | `editor-currency`       | `<select>`                              |
| Tax Rate         | `editor-taxrate`        | `<select>` value `NONE` = 0%            |

## Date format: `DD-MM-YYYY` — matching the receipt, not ISO

**Always write the date as `DD-MM-YYYY`** (e.g. `31-07-2026`), which is the
format Hubdoc's own date widget displays and the format UK receipts use.

Do **not** use ISO `YYYY-MM-DD`. Verified 2026-08-13: entering
`2026-07-31` did not error — the `date-field` widget silently reformatted
it to `31-07-2026` on change. **That silent correction is the danger, not
a safety net:** it means a wrong-format entry looks like it worked. An
ambiguous date such as `2026-07-08` could be reinterpreted as 8 July or
misread day-for-month with no visible sign of the mistake.

Read the date back after setting it and confirm it matches the receipt's
day and month — do not assume your input format survived.

## Setting field values

```bash
# <input> fields
agent-browser fill "#editor-invoice-number" "2397-5919"

# <select> fields (Document Type, Currency, Tax Rate) — pass the option value
agent-browser select "#editor-document-type" "Receipt"
agent-browser select "#editor-taxrate" "NONE"
```

Document Type option values: `Invoice`, `Receipt`, `Statement`, `Report`,
`CSV`, `Check`, `Deposit`, `eTransfer`, `Invoice (AR)`, `Payment`,
`Credit Memo`, `Purchase Order`, `Other`.

Supplier (`editor-vendor-id`) takes a numeric option value, not the name.
Read the options first, and beware near-identical names — "Companies House"
and "Companies Made Simple" are different suppliers:

```bash
agent-browser eval "JSON.stringify(Array.from(document.getElementById('editor-vendor-id').options).filter(o=>/made simple/i.test(o.textContent)).map(o=>({v:o.value,t:o.textContent.trim()})))"
```

## Total Amount: needs focus → type → blur

`editor-amount` is model-backed (`modelattribute="amount"`). Setting the value
without a real focus/blur cycle leaves the model empty, so **Publish fails
with "This field is required."** even though the field shows the right number.

**Working sequence, verified 2026-08-13:**

```bash
agent-browser click "#editor-amount"              # real focus
agent-browser fill  "#editor-amount" ""           # clear (type appends)
agent-browser type  "#editor-amount" "119.99"     # per-character key events
agent-browser click "#editor-invoice-number"      # blur commits to the model
```

`fill` alone sets the value and clears the required error, but does **not**
commit to the model — the `Total:` line stays blank. The blur is what commits.

Note `click` steals window focus from the user's terminal (see
[`agent-browser-local`](../../agent-browser-local/SKILL.md)) — warn them
before this sequence, or their keystrokes land in the page.

### Verifying: read the `Total:` line

```bash
agent-browser eval "(function(){const n=Array.from(document.querySelectorAll('*')).filter(e=>e.children.length===0&&/^\s*Total:\s*$/.test(e.textContent))[0];return n.closest('div').innerText.replace(/\s+/g,' ').trim();})()"
```

- `Total: 119.99 GBP` → committed, safe to publish.
- `Total: GBP` (no figure) → **not** committed; redo the sequence.

Two things that look like verification but are not:

- **`Subtotal:` and `Tax:`** update from the DOM property, so they show the
  right numbers while the model is still empty.
- **The `value` attribute** lags — it stays at `0.00` after a successful edit
  and only syncs on save. Confirmed by comparing against an already-published
  document, where `value` attribute, property, and `Total:` all agreed.
