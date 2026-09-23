# Manual submission through the project's web form

Hand the prepared draft to the user to paste into the upstream web form
themselves, instead of publishing it through an API or CLI.

## When this is the right channel

Prefer it whenever any of these hold:

- **The tracker applies metadata the API does not.** A GitHub issue form
  (`.github/ISSUE_TEMPLATE/*.yml`) applies its `type:` and `labels:` on
  submission. `gh issue create` bypasses the form, so those must be set by
  hand and are easy to get subtly wrong.
- **Attribution should be the user's.** A submission filed through the user's
  browser session is plainly theirs. Some projects also treat agent-filed
  reports differently.
- **The form has required fields or validation** that only the rendered form
  enforces.
- **The user asks to file it themselves.** Their call, not a decision to argue
  with.

Publishing by API stays fine for a project with no form, or when the user has
asked for the API path specifically.

## Prepare the draft as separable fields

Write the draft so each form field is a self-contained block. For a GitHub
issue form, read the template first and use one block per `textarea` id, in
the template's own order.

Keep the whole draft in one scratch file, with each field under a top-level
Markdown heading naming the form field:

```markdown
# Title

[Feature]: ...

# Problem or use case

...

# Proposed solution

...
```

Then split it into one file per field, so a single mis-paste is recoverable
without regenerating anything:

```bash
python3 - <<'EOF'
import re, pathlib
src = pathlib.Path('issue-draft.md').read_text()
parts = re.split(r'(?m)^# (.+)$', src)
for i in range(1, len(parts), 2):
    slug = parts[i].strip().lower().replace(' ', '-')
    pathlib.Path(f'{i // 2 + 1}-{slug}.txt').write_text(parts[i + 1].strip() + '\n')
EOF
```

The headings are scaffolding for the split. The form supplies its own field
labels, so they are not pasted.

## Drive the paste sequence

1. Open the form with the `open-in-user-browser` skill. Use the template's
   direct URL where one exists, so the user does not have to pick from the
   chooser:

   ```text
   https://github.com/OWNER/REPO/issues/new?template=feature_request.yml
   ```

2. Where the user needs a field-specific hint, such as a template-prefilled
   title that needs select-all, make the file's first line `#NOTE: <text>`.
   The hint appears in the notification and is not copied.

3. Tell the user the sequence is about to start and what to watch for in the
   fields; the notifications only name the field.

4. Run [`scripts/paste-form-fields.sh`](../scripts/paste-form-fields.sh) in
   the foreground on the field files, in form order:

   ```bash
   scripts/paste-form-fields.sh 1-title.txt 2-problem-or-use-case.txt ...
   ```

   For each field it loads the clipboard without a trailing newline, reads
   it back and aborts on a mismatch, then shows a desktop notification naming
   the form field. Notifications stay up for 10 seconds and stack, and the
   script advances every 5 seconds, so the user pastes without reporting back
   between fields. `-f` sets the first delay, `-d` the later ones and `-t`
   the display time, all in seconds; use them when the user asks for a
   different pace.

   It picks `wl-copy`, `xclip`, `xsel` or `pbcopy` to suit the session, and
   `notify-send` or macOS `osascript` for notifications. Under `osascript`,
   macOS decides how long a notification stays up.

5. Name the field file paths once, so the user can re-run the script on a
   single field if a paste goes wrong or they miss a window.

## Before they submit

Ask them to confirm the things only the rendered form reveals:

- issue-number and user references resolved to real links;
- fenced code blocks rendered as code, not reflowed prose;
- the template's `type` and labels actually applied.

## After it is filed

Ask for the resulting URL or number — there is no API response to read it
from. Then verify it landed as intended, and record it wherever the work is
tracked:

```bash
gh api repos/OWNER/REPO/issues/NUMBER \
  --jq '"#\(.number) \(.title)\nstate=\(.state) type=\(.type.name // "none") labels=\(.labels|map(.name)|join(",")) author=\(.user.login)"'
```

## Approval boundary

This path does not relax the boundary in the main skill: the user performs the
publication, so nothing is published without them. Opening the form and
loading the clipboard are preparation, not publication, and need no separate
approval once the draft itself is agreed.
