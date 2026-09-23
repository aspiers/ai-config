# Manual Journals (create / update / void)

Operational notes for `create-manual-journal`, `update-manual-journal`,
`list-manual-journals`. Tool schemas alone are misleading in places;
this file captures the actual API behaviour learnt the hard way.

## `lineAmountTypes` — never pass `NO_TAX`

The tool schema offers `EXCLUSIVE | INCLUSIVE | NO_TAX`, but the Xero
API rejects the literal string `NO_TAX`:

```text
Error converting value "NO_TAX" to type 'Xero.API.Library..LineAmountType'.
Path 'ManualJournals[0].LineAmountTypes'. (ErrorNumber 14,
PostDataInvalidException)
```

The accepted on-the-wire value is `NoTax` (PascalCase), which the
underlying SDK serialises automatically when you omit the field.

**Do this:** simply omit `lineAmountTypes` from the call. The default
behaviour produces `Line Amount Types: NoTax` on the stored record,
which is what you want for VAT-exempt crypto bookkeeping.

`EXCLUSIVE` and `INCLUSIVE` may work as-is — untested in this codebase.

## `update-manual-journal` works on POSTED journals

The tool description says

> Only works on draft manual journals.

This is **incorrect**. `update-manual-journal` happily mutates a POSTED
manual journal in place (narration, date, URL, line items, status).
Confirmed working as of 2026-05-22 against tenant
`a688ebfc-1222-4ed9-982e-74bf27e8b011` (Toucan Protocol Association,
toucan-mcp-server v0.0.16).

This is what makes the **void-and-replace** pattern below tractable
via MCP without dropping into the Xero web UI.

## Void-and-replace pattern

When an existing POSTED MJ is structurally wrong and you want a clean
audit trail (rather than amending in place), void the original and
post a replacement that cross-references it.

### Sequence

1. **Create the replacement first**, POSTED, dated to the original
   economic event date. Narration must reference the about-to-be-voided
   UUID so the audit trail survives.
2. **Verify with `list-manual-journals manualJournalId=<new-uuid>`** —
   the create-tool's response prints the lines as `[object Object]`
   and may render your input params verbatim into the displayed
   narration. Always read back the stored state before trusting it.
3. **Update the original to `status: "VOIDED"`** with a narration that
   points at the replacement UUID. `manualJournalLines` must be
   re-sent (Zod schema requires the array even on a void).

### Why this order

If you void first and the replacement create fails, 1512 (or whatever
account) is left in a worse state than before. Creating the
replacement first means the books stay balanced at every intermediate
step.

## Read-back is non-optional

The create / update tools render their response by interpolating your
input params into a free-form string. Two consequences:

- Line items show as `[object Object]` in the response — useless for
  verification.
- If your tool-call XML is malformed (unclosed tag, mis-named
  parameter), the bad text may end up rendered into the response
  output *and* into the stored record.

So **always** confirm the stored state with
`list-manual-journals manualJournalId=<uuid>` immediately after any
write. Check:

- `Date:` — was your `YYYY-MM-DD` actually parsed, or did Xero default
  to today?
- `Status:` — POSTED / VOIDED / DRAFT as intended?
- `Description:` (= narration) — no leaked XML tags from your tool
  call?
- Line amounts and account codes balance to zero?

Do not assume the write succeeded just because the write call returned
without error.

## Multi-step workflows

A void-and-replace plus follow-on MJs typically takes 4+ tool calls.
The server refreshes its token on demand (see
[`authentication.md`](authentication.md)), so token expiry no longer
interrupts a sequence. If any call fails part-way, re-read state before
resuming, and record each new UUID in your working notes as you go so
the cross-reference chain survives an interruption.
