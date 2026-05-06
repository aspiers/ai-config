# Searching for documents

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
