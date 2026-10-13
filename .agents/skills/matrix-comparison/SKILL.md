---
name: matrix-comparison
description: >-
  Researches and compares alternatives in a ranked, source-linked HTML matrix
  with separate criteria, traffic-light cells and multiple feature filters.
  Use when comparing options, approaches, services, tools, organisations,
  policies or other alternatives, or requesting a comparison matrix. For
  FOSS projects, combine with comparing-open-source-projects for its research
  requirements.
---

# Matrix comparison

Make the decision easy to scan: a short recommendation, then a comparison
matrix. The matrix is the main deliverable, not an appendix to an essay.

## Scope and evidence

- Compare the full set the user requested or already investigated. Preserve
  exact identities, variants and a current baseline when useful. Retain
  rejected, unavailable or out-of-scope candidates with a clear reason.
- Discover more candidates only when requested or needed to answer the brief.
  State shortlist boundaries rather than claiming an exhaustive search.
- Choose criteria from the user's decision, constraints and use case. This
  workflow is not limited to products, purchases, hardware or software.
- Verify changing or disputed facts using appropriate primary sources. Use
  independent experience or evaluation for real-world behaviour. Link each
  claim or group of claims to evidence and give an observation date.
- Distinguish advertised capability, observed behaviour, inference, absence,
  unknown and not applicable. An unlisted feature is not a tested absence.
  Popularity and review scores are evidence inputs, not proof of suitability.
- Preserve exact thresholds, prerequisites and conditions. Do not turn a
  conditional price, licence, eligibility rule or capability into a blanket
  claim. Keep a decision-changing caveat beside the affected value.

## Build the comparison

Rank by the agent's recommendation for the stated use case, explaining the
basis briefly. Put identity, decisive constraints and verdict near the left.
Use a different order when the user requests it or a ranking is not meaningful.
Do not invent aggregate scores by counting green cells.

When a baseline exists, put it first and pin it directly beneath the headers
by default, with a checked "Pin baseline" option. Alternatives scroll directly
underneath it for vertical comparison. Keep the columns needed to identify
rows fixed during horizontal scrolling, including at narrow viewport widths.

Give common decision criteria separate columns. Avoid one crowded "extras"
cell for unrelated capabilities. Keep factual values precise; keep judgement
and uncertainty visible. Use focused facet matrices when one matrix becomes
hard to read, preserving candidates and order across facets.

Read [the reporting contract](references/reporting.md) for layout, colours,
controls, accessibility, output location and verification. Reuse
[the shared template](assets/report-template.html), preferably through the
[renderer](scripts/render.py), rather than rebuilding the interaction code.
Run its `--help` and read [the data interface](references/data.md) when using
structured input. Adapt columns, filters and notes to the domain.

## Domain-specific research

For free and open source software, also use
[comparing-open-source-projects](../comparing-open-source-projects/SKILL.md).
It owns canonical repositories, popularity, maintenance, licence and edition
checks; this skill owns the reusable matrix presentation and interaction.
Other specialist skills can supply domain evidence without duplicating this
reporting contract.

## Finish

Verify the result in a browser, including combined feature filters and narrow
widths. Open the HTML using the available trusted preview or repository opener.
Return a short link to the finished comparison and any material unresolved
limit. Preserve the same report path when refining an existing comparison.
