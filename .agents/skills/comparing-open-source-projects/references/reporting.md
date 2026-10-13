# FOSS comparison reporting requirements

Read [matrix-comparison](../../matrix-comparison/SKILL.md) and its
[HTML reporting contract](../../matrix-comparison/references/reporting.md)
for layout, colours, controls, output handling and verification. The
[shared renderer](../../matrix-comparison/scripts/render.py) and
[data interface](../../matrix-comparison/references/data.md) implement that
contract. This file adds FOSS-specific content, not another HTML workflow.

## Summary and facet matrices

Use `table_id: comparison-summary` and `name_label: Project`. Keep one row
per requested candidate in recommendation order. Include these summary
criteria, in addition to the renderer's rank and project columns:

| Domain fit | GitHub stars | Maintenance | Licence | Recommendation |
| ---------- | -----------: | ----------- | ------- | -------------- |

- Domain fit and recommendation are concise use-case judgements.
- GitHub stars use the exact canonical-repository count and observation date.
  If GitHub is not canonical, show `N/A`; identify mirrors separately. Use a
  numeric cell value only when a comparable count is known.
- Maintenance shows a classification supported by common activity windows,
  exact dates and meaningful activity, not just an automated commit.
- Licence names the governing licence and SPDX identifier where one exists.
  Mark unknown or unclear terms explicitly. Stars and licence identifiers
  remain uncoloured unless accompanied by a suitability judgement.

Add focused facet matrices for capabilities, usability, integrations,
operations or other distinct decision factors when helpful. Reuse the same
rows and order. The renderer gives them `comparison-facet-ID` identifiers.
Capability columns can participate in the shared multi-select feature filter.
Avoid duplicating the summary or calculating a score from coloured cells.

## Candidate evidence

Each candidate needs linked details sufficient to justify the summary:

- Verdict and best fit, relevant domain capabilities and edition boundaries.
- Canonical project/repository and exact popularity observations, including
  mirrors or multi-repository qualifications.
- Maintenance classification, common observation window, latest meaningful
  default-branch commit, stable release, archival/deprecation state and any
  assessed issue/PR responsiveness.
- Governing licence text, SPDX identifier, exceptions, mixed or component
  licensing, and whether the compared edition is actually free/open source.
- Strengths, trade-offs, operational burden and material evidence gaps.
- Direct repository, release, licence and documentation sources, dated where
  appropriate. Unknown evidence stays unknown rather than becoming zero.

Use each row's `details` for this evidence. The shared renderer links summary
and facet names to `candidate-ID` and provides a link back to the summary.
Keep decision-changing licence and maintenance caveats visible in cells;
collapsed details must not hide a blocker.

Include short notes on domain interpretation, named versus discovered
candidates, inclusion criteria, activity window and important exclusions.
Clarify that stars measure attention and that low churn can mean maturity.
Avoid a blanket legal-advice claim; describe licence evidence and its limits.

## Save, verify and open

Default durable reports to `docs/research/` in the current repository, subject
to an explicit user/environment destination. For a new report, use a
`foss-comparison-DOMAIN-SLUG-UTC-TIMESTAMP.html` name. Update the same file when
refining an existing report.

Alongside the shared browser checks, verify every requested candidate appears,
each has the five summary criteria and all required evidence or explicit
unknowns, summary/detail links resolve, and facet identities are unique.

> **AUTHOR-SPECIFIC:** In the maintainer's checkout, the configured opener is
> `~/bin/open`. Other users should use their own trusted HTML opener.

Open the verified report exactly once with that configured opener. If a
report is regenerated at the same path, keep its existing tab. Return a short
link and state whether it was opened or the existing tab was retained.
