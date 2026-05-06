# Fields and JS interaction

All TRANSACTION DETAILS fields are manipulated by ID — do NOT use
`agent-browser fill` with snapshot refs for these fields, as the unlabelled
textboxes are display-only shims and will corrupt other fields (e.g. Supplier).
Always use the JS approach below.

## Field IDs

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
