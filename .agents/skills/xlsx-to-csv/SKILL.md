---
name: xlsx-to-csv
description: >-
  Converts XLSX spreadsheets, including multi-sheet workbooks, into CSV files
  that can be read and grepped directly. Use whenever an .xlsx report needs
  processing — exports from Xero, Cryptio, bank statements, or any tool that
  delivers spreadsheet output.
---

# XLSX to CSV

## When to use

Any time you need to read or grep the contents of an `.xlsx` file in
text form. The `Read` tool cannot render `.xlsx` directly; convert to
CSV first.

## Single-sheet XLSX

LibreOffice headless conversion works:

```bash
libreoffice --headless --convert-to csv --outdir /path/to/outdir /path/to/input.xlsx
```

Output: `outdir/input.csv` (the active sheet only).

## Multi-sheet XLSX

LibreOffice's `--convert-to csv` only emits the **active sheet**, so
hidden sheets get dropped silently. For multi-sheet files use
`xlsx2csv` via `uvx` (no permanent install needed):

```bash
uvx --from xlsx2csv xlsx2csv -a /path/to/input.xlsx /path/to/outdir/
```

Output: one CSV per sheet, named after the sheet (with spaces preserved).

If you don't know whether a file is multi-sheet, default to `xlsx2csv`
— it handles single-sheet files fine too.

## Files served with the wrong extension

Some tools deliver XLSX content with a `.zip` extension (e.g. Cryptio's
Trial Balance download). Inspect with `unzip -l file.zip` — if you see
`xl/workbook.xml` or `[Content_Types].xml`, it's an XLSX. Rename to
`.xlsx` and convert as normal.

## Pitfalls

- LibreOffice silently emits the active sheet only — running it on a
  multi-sheet file looks successful but discards hidden sheets. Always
  check sheet count via `unzip -l file.xlsx | grep worksheets/sheet`.
- `xlsx2csv` requires an output directory for `-a`; it will not write
  to stdout when emitting multiple sheets.
- Empty rows in the source are emitted as commas-only lines; filter
  with `grep -v '^,*$'` if they're noisy.
