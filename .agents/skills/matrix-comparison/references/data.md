# Renderer data interface

Run `python3 scripts/render.py --help` from this skill's directory for the
CLI. It reads a JSON object and writes self-contained HTML. Input errors fail
before an output is written. The renderer escapes text and permits HTTP(S)
source links; do not place raw HTML in input fields.

## Fields

- `title`, `scope`, `observed_at`: visible text, including the observation
  date and any time zone relevant to the research.
- `columns`: ordered objects with unique `key`, `label` and optional `kind`.
  Kinds are `text` (default), `number` or `feature`. Rank and candidate name
  columns are added by the renderer. Name their domain with `name_label`.
- `rows`: ordered candidates with unique `id`, `name`, optional `url`, optional
  `category` (`candidate`, `baseline` or `excluded`) and a `cells` mapping.
  Order is recommendation order, not a computed score.
- Each cell has `text`, optional `status` (`good`, `caution`, `poor`,
  `unknown`, `neutral`), optional numeric `value`, optional boolean `present`,
  optional string `category`, and optional `sources`, an array of
  `{label, url}` objects. Omitted cells
  render as unknown. `present: true` is required to pass a feature filter;
  `false` is known absence and omission means unknown. Colour never implies
  a filter flag. Numeric values use one stated unit; missing values sort last.
- `fixed_columns`: optional count of leading identifying columns to freeze,
  including rank and name. Defaults to `2`; increase it when variant/edition
  columns also distinguish rows. Must be an integer from 2 to the column count.
- `pin_baseline`: optional initial toggle state, default `true`. Rows marked
  `category: baseline` appear first and remain sticky beneath the header while
  other rows scroll. The checked control exempts them from filters and sorts.
  Unchecking restores ordinary behaviour; multiple baselines stack. A report
  with no baseline has no pin control.
- `picks`: optional `{label, row_id, summary}` recommendations.
- `notes`: optional `{label, text, sources}` qualifications or method notes.
- `numeric_filters`: optional `{key, label, options}` constraints. Each option
  has a label and numeric `max`, with optional `exclusive: true`. No option
  selected means no constraint; unknown values fail an active constraint.
- `categorical_filters`: optional `{key, label, options}` selectors referencing
  a known column. Each option has `label` and a nonempty `values` array of
  exact cell-category strings. Group several values in one option where
  useful. Use `null` to explicitly match cells without a known category.
  The default "Any" imposes no category constraint. Category labels and
  suitability colours are independent; do not infer either from the other.
- `facets`: optional `{id, title, columns}` extra matrices using the same rows
  and cells. Column objects follow the main-column contract.
- A row's optional `details` is an array of `{label, text, sources}` facts or
  evidence sections, linked from its name. Keep load-bearing caveats in cells
  as well. Summary/detail fragment IDs derive from each unique row ID.
- `table_id` defaults to `comparison-summary`. Facets use
  `comparison-facet-ID`; candidate details use `candidate-ID`.

The example below uses fictional organisational approaches, not products or
verified recommendations. Extend it with more criteria and candidates.

```json
{
  "title": "Decision-making approaches",
  "scope": "Illustrative comparison for a small team",
  "observed_at": "Illustrative data, not current research",
  "name_label": "Approach",
  "columns": [
    {"key": "verdict", "label": "Recommendation"},
    {"key": "async", "label": "Asynchronous", "kind": "feature"},
    {"key": "audit", "label": "Decision record", "kind": "feature"}
  ],
  "rows": [
    {
      "id": "written-proposal",
      "name": "Written proposal",
      "cells": {
        "verdict": {"text": "Useful for considered decisions", "status": "good"},
        "async": {"text": "Yes", "status": "good", "present": true},
        "audit": {"text": "Yes", "status": "good", "present": true}
      }
    },
    {
      "id": "live-discussion",
      "name": "Live discussion",
      "cells": {
        "verdict": {"text": "Useful when discussion is urgent", "status": "caution"},
        "async": {"text": "No", "status": "poor", "present": false},
        "audit": {"text": "Only if documented", "status": "caution"}
      }
    }
  ]
}
```
