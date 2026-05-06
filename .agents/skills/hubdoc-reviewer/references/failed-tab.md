# Processing the Failed Tab


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
