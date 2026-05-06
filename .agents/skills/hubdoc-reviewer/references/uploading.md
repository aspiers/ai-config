# Uploading documents


1. Click the "Upload Document" button
2. In the upload modal, set the file on the hidden file input:
   ```bash
   agent-browser upload "#upload-modal input[type='file']:not(#file-upload)" /path/to/file.pdf
   agent-browser wait 5000
   ```
3. Verify the upload completed by checking the document list for the new entry
4. **Close the upload modal** — it does not close automatically. Click the
   X button (link "X" ref) or the close button to dismiss it. If the modal
   is left open it will interfere with subsequent interactions.

## Downloading and reading Hubdoc PDFs
