# Uploading documents


1. Click the "Upload Document" button
2. In the upload modal, set the file on the hidden file input:
   ```bash
   agent-browser upload "#upload-modal input[type='file']:not(#file-upload)" /path/to/file.pdf
   agent-browser wait 5000
   ```
3. Read the modal: each file is listed with its result, e.g.
   `Invoice.pdf - 403 Forbidden` on failure. Then verify the new entry in
   the document list.
4. **Close the upload modal**: it does not close automatically, and
   `Escape` does not close it either. Click its close button by selector,
   then confirm it is hidden:
   ```bash
   agent-browser click "#upload-modal button.close-modal"
   agent-browser eval "getComputedStyle(document.querySelector('#upload-modal')).display"   # "none"
   ```
   Do **not** use the `link "X"` ref: that X sits next to each listed file
   and removes the file from the upload list; the modal stays open. The
   close button (a red circled ×, top right) has no snapshot ref. If the
   modal is left open it will interfere with subsequent interactions.

## Upload refused with 403 Forbidden (Akamai edge)

Hubdoc sits behind Akamai, which can refuse an upload at the edge even
while browsing and searching work. Confirm the source before drawing
conclusions:

```bash
agent-browser network requests --status 400-499    # find the POST .../api/upload
agent-browser network request <requestId> --json   # inspect the response
```

An Akamai refusal is a bare HTML `403 Forbidden` page that embeds the bot
sensor script, with an `x-akamai-transformed` response header; Hubdoc's own
errors come back inside the app. Do not retry or try to evade the block:
it is a deliberate control. **Do not assume it targets the automated
browser** — the same refusal has hit the user's own browser. Email the file
to the Hubdoc inbox address shown in the upload modal (emailed documents
bypass the web upload path), then continue reviewing and publishing once
the document appears.

Evidence (2026-10-06): uploading one two-page supplier invoice PDF
returned 403 from the Akamai edge in agent-browser **and** in the user's
regular Chrome, which had never seen this error before; emailing the same
file to the Hubdoc inbox worked. Trigger unknown: something in that file,
or an edge-side change affecting all uploads. Distinguish by whether other
files also fail.

## Downloading and reading Hubdoc PDFs
