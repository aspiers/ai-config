# HTML reporting contract

Read this file completely before producing a project comparison report.

## Location and file name

Resolve the current repository rather than the skill's own repository:

```bash
repo_root=$(git rev-parse --show-toplevel)
stamp=$(date -u +%Y-%m-%d-%H%M%SZ)
report_dir="$repo_root/docs/research"
mkdir -p "$report_dir"
html_report="$report_dir/foss-comparison-DOMAIN-SLUG-$stamp.html"
```

Derive `DOMAIN-SLUG` by lowercasing the domain, replacing each run of
non-alphanumeric characters with `-`, and trimming surrounding hyphens. Never
write the report to `/tmp`, a repository's temporary directory, the skill
directory, or a global reports directory. Use a new timestamp rather than
overwriting an earlier comparison.

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

Apply traffic-light styling to summary cells where the report makes a relative
judgement, normally domain fit, maintenance, and recommendation. Leave raw
facts such as star counts and licence identifiers uncoloured unless the cell
also states an explicit suitability judgement.

## Additional facet matrices

The summary table is mandatory, but it need not be the only matrix. Add one or
more focused matrices after the summary and before the detailed project
sections when separate facets would otherwise make the summary too dense or
hide important trade-offs. Useful facets can include capabilities, usability,
operations and security, integration, or ecosystem and maintenance. Do not add
extra matrices when they would merely repeat the summary or detailed prose.

For every additional matrix:

- give it a concise heading and caption;
- use `id="comparison-facet-SLUG"`, deriving `SLUG` with the same rules as
  project fragments;
- keep candidates as rows in the summary's order where practical, and link
  each project name to its detailed section;
- group only comparable criteria in the same matrix and explain ambiguous
  terms nearby;
- keep cells concise, with qualifications and evidence in the detailed
  sections; and
- do not manufacture an aggregate score from coloured cells unless the user
  supplied an explicit weighting model.

Use traffic-light cell ratings only for ordinal judgements tied to the user's
needs:

- `rating-good` (green): relatively strong, suitable, or low concern;
- `rating-caution` (amber): mixed, conditional, or a material trade-off;
- `rating-poor` (red): relatively weak, unsuitable, or a blocker; and
- `rating-unknown` (purple): unknown, unclear, or not comparable.

Every rated cell must contain a concise textual judgement such as “Strong”,
“Mixed”, “Weak”, or “Unknown”; colour is supplementary and must never carry the
meaning alone. Leave factual or categorical cells uncoloured when no honest
ordinal interpretation exists. Assess ratings against the stated use case,
not a universal ranking, and explain surprising ratings in the detail section.

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
- Include the visible traffic-light legend from the template whenever any
  matrix cells are rated.
- Keep rating colours supplementary: every coloured cell must communicate its
  judgement in text and remain understandable without colour.
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

1. its resolved path is inside `$repo_root/docs/research/` and it is non-empty;
2. no `{{PLACEHOLDER}}` tokens remain;
3. it contains the summary table and all six required headers;
4. every project link in the summary and facet matrices has exactly one
   matching detail `id`, every detail section has a summary-table link, and all
   IDs are unique;
5. every additional matrix has a unique `comparison-facet-` ID, heading, and
   caption;
6. every rated cell uses one of the four defined rating classes, contains a
   textual judgement, and has a visible legend in the report;
7. each candidate has stars, maintenance, and licence evidence or an explicit
   unknown value; and
8. the HTML has no remote executable or presentation assets.

Opening the file is not evidence that these checks passed.

> **⚠️ AUTHOR-SPECIFIC:** This public repository's requested local opener is
> `~/bin/open`. Other users must substitute their own trusted HTML opener rather
> than assuming this path exists.

For this repository, open the verified report exactly once:

```bash
~/bin/open "$html_report"
```

Do not use bare `open`, `xdg-open`, a browser command, or a temporary report
path. If the report is regenerated at the same path, leave the existing tab in
place rather than opening a duplicate. End the response with the absolute
report path and state whether it was opened now or an existing tab was left in
place.
