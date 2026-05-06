# Downloading and reading Hubdoc PDFs

document and read the PDF directly.

Workflow:

1. Open the document in the normal Hubdoc UI.
2. Use `snapshot -i -C` and identify the `Download` link/button from the
   document action bar.
3. Prefer downloading to an explicit absolute path under the repository's
   `tmp/` directory.
4. Use the **working sequence** below:

```bash
agent-browser click @eN
agent-browser wait --download "$PWD/tmp/document.pdf"
```

Do **not** assume `agent-browser download @eN /path` will always yield a
readable flat file in Hubdoc. The verified reliable method for Hubdoc is the
click-plus-wait flow above.

5. **Immediately verify the artifact on disk.** Do not assume the success
   message means the file is readable at the requested path.
6. Inspect the saved path. In Hubdoc, the download may appear as a wrapper
   directory at the requested path containing the actual downloaded file.
7. Be aware that Hubdoc download behavior is inconsistent across documents:
   some downloads materialize as the wrapper directory above, while others
   report success but do not appear at the requested path. If that happens,
   stop assuming the download worked and fall back to the on-page screenshot /
   visible text for the current task unless the PDF is essential.
8. Read the resulting PDF content from the downloaded artifact when the file
   is actually present.

Do this instead of guessing route/date details from partial preview text.

## Searching for documents
