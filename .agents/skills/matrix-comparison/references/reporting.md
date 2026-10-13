# HTML matrix reporting contract

## Content and delivery

Default to a standalone HTML document with inline styling and scripts, no
remote executable or presentation assets, and ordinary source links. Use
`assets/report-template.html` as the common presentation and interaction
source. `scripts/render.py` fills it from the documented structured input.

Lead with a short recommendation and the scope/observation date. Put the
ranked matrix before optional detail. A few use-case recommendations help
when there is no single best choice. Do not duplicate the matrix in lengthy
prose. Retain all requested candidates, a useful baseline and clear reasons
for exclusions. Link claims directly in cells or adjacent candidate details.

Store durable reports under `docs/research/` in the current repository unless
user instructions or the environment specify another deliverable directory.
In a projectless task, use its durable output directory. The skill directory
and temporary files are not report destinations. Open the finished artifact
with a trusted available preview or the repository's configured opener.
Update an existing report in place when the user is refining it; do not
create duplicate tabs. Never publish or send the report without authority.

## Matrix layout

- Separate popular or decisive capabilities into individual columns. Put
  identity, constraints and concise recommendation near the left. Raw facts
  and qualifications must survive formatting changes.
- Use semantic tables, captions, column headers, readable text and focus
  indicators. Keep the report usable without relying on hover or colour.
- The table and its section fit the available width. Do not impose a fixed
  pixel width, minimum width or fixed pixel widths for every column. Allow
  cells to wrap and adapt relative column proportions to the content.
- Keep headers and the leading columns required to distinguish rows fixed
  during scrolling. Include variant/edition identifiers when names alone are
  ambiguous. Measure column offsets on resize; do not disable identity-column
  stickiness just because the viewport is narrow.
- When there is a baseline, put it first and pin it below the headers with a
  checked "Pin baseline" control by default. Alternatives must scroll directly
  beneath it so any row can be positioned vertically adjacent to it. Compute
  header and baseline offsets from their rendered heights, not pixel guesses.
  Keep row/column intersections opaque and correctly layered. Add temporary
  scroll-tail space while pinned so even the final alternative can reach the
  baseline; remove that space when unpinned and when printing.
- If fitting all columns produces unreadable cells, offer optional column
  visibility or focused facet matrices. Do not silently drop criteria or
  restore a forced minimum width.
- Support light/dark preferences, local/offline use, and printing. Preserve
  links and all detail when printing.

## Accessible traffic lights

Colour communicates a judgement against the user's needs, not a universal
score. Use a visible legend and text in every coloured cell:

- `good`, green: suitable, useful or an established requested capability.
- `caution`, amber: conditional, limited or a trade-off.
- `poor`, red: a relevant missing capability, serious drawback or blocker.
- `unknown`, amber with explicit text: unverified or not comparable.
- `neutral`, uncoloured: raw fact or not applicable without a fair ordinal
  judgement.

Do not label missing evidence red as though it proved failure. Label "not
advertised" distinctly from "absent". A present feature can still be poor in
practice; its positive filter flag and suitability colour are independent.
Leave categorical facts uncoloured unless you state a use-case judgement.
Avoid arbitrary universal review-score or popularity thresholds. If useful
thresholds are chosen, explain them and keep them separate from ranking.

## Controls

Provide search, recommendation order and useful numeric sorts. Include
numeric constraint filters only when they apply to the domain; cost/budget
is not assumed. Preserve units, boundary inclusivity and unknown values.

Feature requirements use labelled checkboxes or an accessible multi-select,
not a single-choice dropdown. **Match all selected requirements (AND)** by
default and state this beside the controls. No selected features means no
feature constraint. Combine search, numeric limits and selected requirements
with AND. Unknown capability does not satisfy a positive requirement.

A pinned baseline stays visible regardless of search, feature requirements,
numeric filters or sort order. Label this exception. When pinning is disabled,
the baseline follows ordinary filtering, sorting and scrolling. Hide the
control when no baseline exists. Reset restores the initial checked state.
For multiple baselines, place them first and stack their sticky offsets.

Show selected-feature and matching-row counts. Reset clears every control,
restores recommendation order and restores all candidates. A zero-result
selection displays a clear empty state. Keep all filtering local.

## Verification

Check candidate coverage, IDs, source targets, exact values and caveats. Check
escaping and allow only safe source URL schemes. Replace all template tokens.
Do not embed researched markup, scripts, credentials or browsing state.

Run the rendered report in a browser. Verify an individual and multiple
requirements, deselection, reset, search, numeric boundaries, unknown values,
ordering and zero results, including when only a pinned baseline remains.
Check pin/unpin, baseline-first sorting and filters, scrolling an alternative
adjacent to the baseline, and row/column intersections after resize.
Verify table containment and readability at desktop
and narrow widths, sticky elements, light/dark colours and absence of script
errors. An opened file is not evidence that these checks passed.
