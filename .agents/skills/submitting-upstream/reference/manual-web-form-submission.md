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

2. Detect the clipboard tool once, and match it to the session rather than
   assuming: `wl-copy` for Wayland, `xclip -selection clipboard` for X11.

   ```bash
   echo "session=${XDG_SESSION_TYPE:-unset}"
   for c in wl-copy xclip xsel; do command -v "$c" >/dev/null 2>&1 && echo "found: $c"; done
   ```

3. Copy the first field, then **read the clipboard back and show what it
   holds**. A silent copy failure otherwise surfaces as the user pasting stale
   content into a public tracker.

   ```bash
   xclip -selection clipboard < 1-title.txt
   xclip -selection clipboard -o | head -6
   ```

4. Tell the user which field to paste into, how many remain, and what to watch
   for in this particular field — a template-prefilled title needing
   select-all, or a block whose fenced code should be checked in Preview.

5. Wait for the user to say they are ready, then copy the next field. One
   field per turn. Never copy ahead: the clipboard holds one thing, and
   pre-copying destroys the field they are still pasting.

6. Name the scratch file paths once, so the user can grab a field directly if
   a paste goes wrong.

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
