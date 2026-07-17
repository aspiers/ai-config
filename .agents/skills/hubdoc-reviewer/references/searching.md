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

## Normal search vs ADVANCED search — they submit differently

**The advanced search panel HAS a Search button. Click it.**

| | Normal search (top search box) | Advanced search panel |
|---|---|---|
| Submit by | pressing `Enter` in the textbox | **clicking `button "Search"`** |
| Search button | none — there is no longer one | **exists, plainly labelled** |

Do NOT carry the "there is no Search button" fact over from the normal
search to the advanced panel — it applies ONLY to the normal search.

```bash
agent-browser click @e5                  # magnifying glass -> advanced panel
agent-browser wait 2000
agent-browser snapshot -i -C             # find BOTH the field AND the button
agent-browser fill @e6 "search term"     # "Has the Words"
agent-browser scrollintoview @e16        # the Search button
agent-browser click @e16                 # <- REQUIRED. Enter alone does nothing here.
agent-browser wait 4000
```

**Symptom of getting this wrong:** the term visibly appears in the "Has the
Words" textbox (a snapshot confirms `Has the Words: <your term>`) but the
document list never changes — it keeps showing the same unfiltered docs. That
is not a "no results" state and not a stale list; the query simply never ran.

**When snapshotting for the button, do not grep only for textboxes.** A grep
written for the expected field names will hide the Search button from you.
Grep for `button` and read what is actually there. Evidence (2026-07-17): two
searches were declared "not filtering", and the March doc wrongly suspected of
being absent, purely because `button "Search" [ref=e16]` was never looked for.

**Only once the search has actually RUN:** if no results appear in the
document list, the document is not in Hubdoc.

## Process
