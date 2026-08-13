---
name: open-in-user-browser
description: Open a URL or local file in the user's regular browser, including live-rendered local Markdown. Use for `/open` or when the user asks to view a target outside the agent browser.
---

# Open in the user's browser

> **⚠️ AUTHOR-SPECIFIC:** The helper paths below belong to the maintainer's
> deployed environment. Other users must substitute equivalent trusted tools.

If no target was supplied, infer the URL or file most likely intended from the
recent conversation instead of asking for confirmation.

- For an existing local regular file ending in `.md` (case-insensitively), run
  `~/bin/emacs-markdown-live-preview` with the target as one shell argument.
- For every other target, run `~/bin/open` with the target as one shell
  argument.

Run the selected command once, then report the target opened.
