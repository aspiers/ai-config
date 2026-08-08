---
description: "Open a URL or file, inferring it from recent conversation if omitted"
argument-hint: "[URL-or-file]"
---

# Open a URL or file

Open the requested URL or file by running `~/bin/open` with the target as one
shell argument.

The user's optional target is: `$ARGUMENTS`

If the target is empty, select the URL or file from the recent conversation
that the user is most likely referring to. Do not ask for confirmation. Run
the command once, then report the target you opened.
