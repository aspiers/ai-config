---
description: Open a URL or file, inferring it from recent conversation if omitted
argument-hint: "[URL-or-file]"
---

# Open a URL or file

The user's optional target is: `$ARGUMENTS`

If the target is empty, select the URL or file from the recent conversation
that the user is most likely referring to. Do not ask for confirmation.

- For an existing local regular file whose name ends in `.md`
  (case-insensitively), run `~/bin/emacs-markdown-live-preview` with the target
  as one shell argument.
- For every other target, run `~/bin/open` with the target as one shell
  argument.

Run the selected command once, then report the target you opened.
