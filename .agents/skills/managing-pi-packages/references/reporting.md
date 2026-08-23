# Reporting and package notes

Read this file completely whenever an audit report is required or package state changes.

## Report

Begin with a one-line count by verdict, followed by a summary table with one
row per candidate:

```markdown
| Package | Change | Verdict | Status | Action | Key reason |
|---|---|---|---|---|---|
| [name](#package-SLUG) | change | verdict | status | action | reason |
```

Group rows by completion state: put every pending, deferred, or otherwise
incomplete candidate first, followed by every completed upgrade, install,
uninstall, configuration fix, or other resolved action at the end of the
table. Preserve a stable, useful order within each group. A completed row must
remain in the report with its details and status; never remove it merely to
make the pending work more prominent.

The `Status` cell must combine change state with current activation state.
Whenever all relevant resources are filtered or disabled, append `· Disabled`
(for example, `Not applied · Disabled` or `✓ Applied · Disabled`). Use
`Partially disabled` when only some declared resources are filtered.
Distinguish `Inactive`—installed and loaded but not selected in a chain or
configuration—from `Disabled`, which means Pi will not load the relevant
resource. Check both Pi package filters and extension-manager disabled-item
configuration. Do not
let disabled status improve the safety verdict; it only describes exposure.

Make the package cell in every row link to its detailed section. Derive
`<slug>` by lowercasing the package identity, replacing each run of
non-alphanumeric characters with `-`, and trimming surrounding hyphens. Put an
explicit inline anchor at the start of the corresponding heading so Markdown
renderer slug rules cannot break the link. Make the package name in the
heading link to the package's official page. Prefer a verified
`https://pi.dev/packages/<package-identity>` page. If Pi's directory has no
page, as can happen for a Git bundle or unlisted package, use the target
manifest's `homepage`, then the canonical Git repository, and use the npm
package page only as a final fallback:

```markdown
## <span id="package-SLUG"></span>[`PACKAGE`](OFFICIAL-PAGE) …
```

Use these HTML badge templates in the Markdown table and detailed headings,
selecting the context-appropriate verb first. They survive HTML export while
remaining readable as text in Markdown-aware viewers:

- `Appears safe to upgrade/install`: `<span
  style="color:#22c55e;font-weight:700">● Appears safe to
  upgrade/install</span>`
- `Upgrade/Install with caution`: `<span
  style="color:#f59e0b;font-weight:700">● Upgrade/Install with
  caution</span>`
- `Do not upgrade/install`: `<span style="color:#ef4444;font-weight:700">● Do
  not upgrade/install</span>`
- `Inconclusive`: `<span style="color:#a78bfa;font-weight:700">●
  Inconclusive</span>`

In each badge, replace the slash form with the single context-appropriate
verb; never print a literal `upgrade/install` label.

Then write one compact section per package:

```markdown
## <span id="package-SLUG"></span>[`PACKAGE`](OFFICIAL-PAGE) …

- **Status:** <change state plus Disabled/Partially disabled/Inactive if true>
- **Decision:** <Upgrade/Install now, after X, Defer until X, or Do not>
- **Before change:** <exact preparation, using the applicable verb>
- **After change:** <verification and rollback/removal trigger>
- **Actual changes:** <concise summary of code and dependency behavior>
- **Risk/compatibility:** <material findings, or "No material issue found">
- **Why this matters:** <plain-language user impact and realistic trigger>
- **Changelog check:** <classification and any omissions/contradictions>
- **Evidence:** <npm versions and integrity, or Git commits; key files read>
```

Keep routine findings brief, but include enough evidence to justify the
verdict. `Why this matters` is mandatory for every `Do not upgrade` or `Do not
install` verdict and optional otherwise. It must be understandable without
knowing the package architecture: state what the user could lose, expose,
execute, corrupt, or have behave differently, and under what ordinary action
that consequence could occur. Put actionable `Do not` and `Inconclusive`
results first when that helps the user. Mention filtered/disabled state as
exposure context, not as verdict justification.

Capture full npm integrity values in the evidence artifact; abbreviate them in
the human report unless the user requests reproducible full hashes. For Git,
report short commits but retain full commits, origin, selected ref, and
ancestry in evidence. Distinguish "no material issue found" from proof of
safety.

### Update the package-notes inventory

After auditing a named package or applying any package state change, update its
existing entry—or add one if missing—in the durable package-notes file when an
existing location is known. Record the date, exact version/source, decision,
activation state, material behavior and risks, applied configuration, and
report paths when an audit report exists. Update an existing package heading
rather than creating a duplicate. Do not copy credentials, private registry
URLs, or other sensitive evidence into notes.

For a user-waived audit, create no audit verdict/report. Instead record
`NOT AUDITED — explicit user override`, what was installed or changed, the
limited post-install checks, material warnings observed during installation,
and rollback. Do not imply that identity/version checks reviewed the payload.

Resolve the notes path in this order:

1. `$PI_PACKAGE_NOTES` when set.
2. `$PI_EXTENSION_AUDIT_NOTES` as a backward-compatible fallback.
3. The author-specific fallback below.

Update a candidate path **if and only if it is an existing regular file**.
Never create a notes file or its parent directories as a package-management
side effect. If no candidate exists, skip the notes update and state that.

> **⚠️ AUTHOR-SPECIFIC:** In the author's environment, the fallback inventory
> is `~/org/notes/PiAgent.org`. If that file exists, update it automatically in
> both relevant places:
>
> 1. Under `* package audits`, update or add the package heading with the
>    historical decision/evidence described above. Preserve older decisions
>    when they remain useful history.
> 2. In the relevant operational category (for example, workflows,
>    orchestration, or tools), add or update the exact pinned `pi install`
>    command and a concise purpose/status comment. On removal, make this
>    operational inventory reflect that the package is no longer installed
>    without deleting its historical audit entry.
>
> Never create this file if it is absent. Other users must configure their own
> existing notes path or skip this step; the author's path and Org structure
> are not general Pi conventions.

### Persist and open the report

Always save both Markdown and self-contained HTML, even when no candidates are
available. Use a UTC timestamp so repeated audits never overwrite each other:

```bash
report_dir="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/audit-reports"
stamp=$(date -u +%Y-%m-%d-%H%M%SZ)
mkdir -p "$report_dir"
markdown_report="$report_dir/pi-package-audit-$stamp.md"
html_report="$report_dir/pi-package-audit-$stamp.html"
```

1. Write the complete report to `$markdown_report`.
2. Call `preview_export` with `source: "file"`, `format: "html"`,
   `path: "$markdown_report"`, `outputPath: "$html_report"`, and
   `open: false`. The HTML must come from the saved Markdown so both artifacts
   contain the same report.
3. Require a concise, plain-text Markdown H1 suitable for a browser tab title.
   Replace `preview_export`'s generic `<title>` with that H1, and remove the
   generated `<base href="..." />` element. The base directory URL makes
   fragment-only links resolve against the directory rather than the report
   when opened through `file://`:

   ```bash
   python3 - "$markdown_report" "$html_report" <<'PY'
   from html import escape
   from pathlib import Path
   import re
   import sys

   markdown_path = Path(sys.argv[1])
   html_path = Path(sys.argv[2])
   markdown = markdown_path.read_text()
   text = html_path.read_text()

   heading = re.search(r'^#\s+(.+?)\s*$', markdown, flags=re.M)
   if heading is None:
       raise SystemExit('Markdown report has no H1 for the page title')
   page_title = heading.group(1)

   text, title_count = re.subn(
       r'<title>.*?</title>',
       f'<title>{escape(page_title)}</title>',
       text,
       count=1,
       flags=re.S,
   )
   if title_count != 1:
       raise SystemExit(f'expected one title element, replaced {title_count}')

   text, base_count = re.subn(
       r'^<base href="[^"]*" />\n?',
       '',
       text,
       count=1,
       flags=re.M,
   )
   if base_count != 1:
       raise SystemExit(f'expected one base element, removed {base_count}')
   html_path.write_text(text)
   PY
   ```

4. Verify that both files are non-empty, the HTML `<title>` exactly matches
   the Markdown H1, the generic `Markdown Preview` title is absent, the HTML
   has no `<base>` element, and it contains the summary table, verdict colour
   values, and one matching `href`/`id` pair per candidate. Do not claim
   success from a returned path alone.
5. Open the verified HTML report with `open(1)` only once:

   ```bash
   open "$html_report"
   ```

   Track whether this exact report was already opened during the current
   workflow. When updating and regenerating a previously opened report, do
   not call `open` again: that creates duplicate tabs for the same file. Leave
   the existing tab in place so it can be refreshed. A new timestamped report,
   or a report not yet opened, should still be opened after verification.
6. End the response with both absolute artifact paths and state whether the
   HTML was opened now or the existing report tab was left in place.

Pi's renderer supplies theme colours when displaying Markdown, but those
colours are not stored in the `.md` file. The inline verdict colours and HTML
artifact are therefore required for a durable coloured report. If
`preview_export` or `open(1)` is unavailable, retain the Markdown report and
state precisely which persistence step is blocked; do not silently substitute
another opener.

If no matching candidates are available, say so and list named packages that
were pinned, local, missing, or already current in both artifacts.
