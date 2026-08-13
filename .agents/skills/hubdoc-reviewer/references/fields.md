# Fields and JS interaction

All TRANSACTION DETAILS fields are manipulated by ID — do NOT use
`agent-browser fill` with snapshot refs for these fields, as the unlabelled
textboxes are display-only shims and will corrupt other fields (e.g. Supplier).
Use the JS approach below.

**Exception: `editor-amount` is model-backed and JS value-setting does not
reach its model** — the field looks correct but Publish rejects it as
required. See "Total Amount" below before setting it.

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

## Total Amount: JS value-setting does NOT reach the model

**`editor-amount` cannot be set by assigning `.value` from JS.** The field is
model-backed:

```html
<input type="text" id="editor-amount" name="editor-amount"
       value="0.00" modelattribute="amount">
```

Assigning `.value` updates the DOM property only. The HTML `value` attribute
and the `modelattribute="amount"` model stay at `0.00`, and Hubdoc's
validator reads the model — so **Publish fails with "This field is
required."** even though the field visibly shows the right number.

Verified 2026-08-13: `.value` read back `119.99` while
`getAttribute('value')` still read `0.00`. A full `focus` → `input` →
`keyup` → `change` → `blur` dispatch did not close the gap, and no
Backbone/jQuery handle was exposed on the page to write the model directly.

### Detecting the failure

Two independent tells, both cheap:

```bash
# 1. property vs attribute disagree => the model was never updated
agent-browser eval "(function(){const a=document.getElementById('editor-amount');
  return JSON.stringify({prop:a.value, attr:a.getAttribute('value')});})()"

# 2. the Total: summary line renders with no figure (bare "Total: GBP")
```

The blank `Total:` line is a **symptom of this bug**, not a cosmetic quirk —
`#edit-data-total-container` stays unpopulated precisely because the model
never received the amount. Do not dismiss it. (`Subtotal:` and `Tax:` DO
update from the DOM property, so they can look correct while the model is
still empty — they are not sufficient verification on their own.)

### Working around it

Native typing produces real key events and is the documented path for
model-backed widgets, but note that `click` steals window focus from the
user's terminal (see the `agent-browser-local` skill) — warn them first, or
they will type into the page. If native typing also fails to write through,
ask the user to enter the amount by hand rather than retrying; two failed
attempts is the stop point.

Always confirm with the property/attribute check above before publishing.
