# HTML reporting contract

Read this file completely before producing a project comparison report.

## Location and file name

Resolve the current repository rather than the skill's own repository:

```bash
repo_root=$(git rev-parse --show-toplevel)
stamp=$(date -u +%Y-%m-%d-%H%M%SZ)
mkdir -p "$repo_root/tmp"
html_report="$repo_root/tmp/foss-comparison-DOMAIN-SLUG-$stamp.html"
```

Derive `DOMAIN-SLUG` by lowercasing the domain, replacing each run of
non-alphanumeric characters with `-`, and trimming surrounding hyphens. Never
write the report to `/tmp`, the skill directory, or a global reports directory.
Use a new timestamp rather than overwriting an earlier comparison.

## Required structure

Use `assets/report-template.html` as the basis for a complete, self-contained
HTML document. Replace every template placeholder and remove illustrative
comments. Keep all styling inline so the report remains usable as a local
file.

After the title and a short scope/as-of line, put the summary table before the
detailed analysis. It must have `id="comparison-summary"` and one row per
candidate, with these columns:

| Project | Domain fit | GitHub stars | Maintenance | Licence | Recommendation |
| ------- | ---------- | -----------: | ----------- | ------- | -------------- |

The project name in each row must link to that project's detailed section.
Derive the fragment as `project-SLUG`, where `SLUG` is the lowercased project
name with runs of non-alphanumeric characters replaced by `-` and surrounding
hyphens removed:

```html
<a href="#project-example">Example</a>
<section class="project-detail" id="project-example">
```

Keep the summary compact. Show the exact observed star count, a concise
maintenance classification, and the licence identifier in the table; put
qualifications in the detailed section. Use `N/A`, `Unknown`, or `Unclear`
rather than a misleading zero.

## Detailed project sections

Create one detailed section for every summary row, in the same order. Each
section must make the recommendation and its evidence understandable without
reading other sections. Include:

- **Verdict and best fit:** concise recommendation and intended user profile.
- **Domain fit:** relevant capabilities, edition/component boundaries, and
  significant missing features.
- **Popularity:** canonical repository, exact GitHub stars, observation date,
  and any mirror or multi-repository caveat.
- **Maintenance:** classification plus exact supporting dates/counts for the
  common activity window, latest stable release, latest meaningful commit,
  archival/deprecation state, and responsiveness evidence when assessed.
- **Licence:** exact licence and linked governing text, practical high-level
  implications, exceptions or mixed licensing, and whether the compared
  edition is actually free and open source.
- **Strengths and trade-offs:** project-specific benefits, risks, operational
  burden, ecosystem, and evidence gaps.
- **Evidence:** direct links to the canonical repository, releases, licence,
  documentation, and other sources used, with an as-of date.

End each detailed section with a link back to `#comparison-summary`.

After the project sections, include a short methodology and shortlist section.
State the domain interpretation, user-supplied versus discovered candidates,
inclusion criteria, activity window, important exclusions, and limitations of
stars and maintenance proxies. Finish with a comparative recommendation that
is explicitly tied to the user's needs.

## Presentation and claims

- Use semantic HTML, a plain-text `<title>`, a single `<h1>`, accessible link
  text, and visible focus styles.
- Keep verdict colours supplementary: the text must communicate meaning
  without colour.
- Use human-readable exact counts such as `24,381`, not false precision copied
  from rounded badges.
- Put an explicit UTC date beside volatile data. Do not call figures “current”
  without an observation date.
- Cite sources with ordinary `https://` links. Remote citations are allowed;
  remote scripts, stylesheets, fonts, and images are not.
- Escape untrusted project names and text before placing them in HTML. Do not
  copy scripts, event handlers, or embedded markup from researched pages.
- Do not include credentials, private paths, browsing session details, or
  unrelated local information.

## Verify and open

Before opening the report, verify that:

1. its resolved path is inside `$repo_root/tmp/` and it is non-empty;
2. no `{{PLACEHOLDER}}` tokens remain;
3. it contains the summary table and all six required headers;
4. every project link in the table has exactly one matching detail `id`, every
   detail section has a table link, and all IDs are unique;
5. each candidate has stars, maintenance, and licence evidence or an explicit
   unknown value; and
6. the HTML has no remote executable or presentation assets.

Opening the file is not evidence that these checks passed.

> **⚠️ AUTHOR-SPECIFIC:** This public repository's requested local opener is
> `~/bin/open`. Other users must substitute their own trusted HTML opener rather
> than assuming this path exists.

For this repository, open the verified report exactly once:

```bash
~/bin/open "$html_report"
```

Do not use bare `open`, `xdg-open`, a browser command, or `/tmp`. If the report
is regenerated at the same path, leave the existing tab in place rather than
opening a duplicate. End the response with the absolute report path and state
whether it was opened now or an existing tab was left in place.
