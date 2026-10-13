#!/usr/bin/env python3
"""Render a domain-neutral comparison matrix from a JSON document."""

import argparse
import html
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

STATUSES = {"good", "caution", "poor", "unknown", "neutral"}
LABELS = {
    "good": "Suitable or present",
    "caution": "Conditional or trade-off",
    "poor": "Drawback or blocker",
    "unknown": "Unknown or unverified",
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_-]*$")


def escape(value):
    return html.escape(str(value), quote=True)


def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid identifier: {value!r}")
    return value


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Expected a number: {value!r}")
    if not math.isfinite(value):
        raise ValueError("Numeric values must be finite")
    return value


def url(value):
    parts = urlsplit(value)
    if parts.scheme not in {"https", "http"} or not parts.netloc:
        raise ValueError(f"Only absolute HTTP(S) source links are allowed: {value!r}")
    return escape(value)


def sources(items):
    return " ".join(
        f'<a href="{url(item["url"])}">{escape(item["label"])}</a>'
        for item in items
    )


def columns(items):
    seen = set()
    for column in items:
        key = identifier(column["key"])
        if key in seen:
            raise ValueError(f"Duplicate column: {key}")
        seen.add(key)
        if column.get("kind", "text") not in {"text", "number", "feature"}:
            raise ValueError(f"Invalid column kind: {key}")
        if not isinstance(column["label"], str):
            raise ValueError(f"Column label must be text: {key}")
    return items


def cell(row, key):
    value = row.get("cells", {}).get(key, {"text": "Not verified", "status": "unknown"})
    if not isinstance(value.get("text"), str):
        raise ValueError(f'Cell text must be a string: {row["id"]}/{key}')
    if value.get("status", "neutral") not in STATUSES:
        raise ValueError(f'Invalid status: {row["id"]}/{key}')
    if "present" in value and not isinstance(value["present"], bool):
        raise ValueError(f'Feature present must be boolean: {row["id"]}/{key}')
    if "category" in value and (not isinstance(value["category"], str) or not value["category"]):
        raise ValueError(f'Category must be nonempty text: {row["id"]}/{key}')
    if value.get("value") is not None:
        number(value["value"])
    return value


def render_cell(value):
    status = value.get("status", "neutral")
    text = escape(value["text"])
    links = sources(value.get("sources", []))
    if links:
        text += " " + links
    if status != "neutral":
        text = (
            f'<span class="cell-status"><i class="dot" role="img" '
            f'aria-label="{LABELS[status]}"></i><span>{text}</span></span>'
        )
    return f'<td class="{status}">{text}</td>'


def matrix(
    rows, cols, table_id, name_label, caption, fixed_columns=2, pin_baseline=True
):
    heads = ["Rank", name_label] + [column["label"] for column in cols]
    proportions = [5, 15] + [80 / len(cols)] * len(cols)
    colgroup = "".join(f'<col style="width:{width:.6f}%">' for width in proportions)
    header = "".join(f'<th scope="col">{escape(label)}</th>' for label in heads)
    rendered = []
    ranks = {}
    rank = 0
    for row in rows:
        if row.get("category", "candidate") == "candidate":
            rank += 1
            ranks[row["id"]] = rank
    if pin_baseline:
        rows = sorted(rows, key=lambda row: row.get("category") != "baseline")
    for row in rows:
        category = row.get("category", "candidate")
        if category == "candidate":
            label = str(ranks[row["id"]])
        else:
            label = category.capitalize()
        name = escape(row["name"])
        if row.get("details"):
            name = f'<a href="#candidate-{row["id"]}">{name}</a>'
        elif row.get("url"):
            name = f'<a href="{url(row["url"])}">{name}</a>'
        rank_class = 'rank' if category == 'candidate' else 'context'
        content = f'<td class="{rank_class}">{escape(label)}</td><td>{name}</td>'
        content += "".join(render_cell(cell(row, column["key"])) for column in cols)
        baseline = category == "baseline"
        pinned = ' class="pinned-baseline"' if baseline and pin_baseline else ''
        rendered.append(f'<tr data-id="{row["id"]}" '
                        f'data-baseline="{str(baseline).lower()}"{pinned}>{content}</tr>')
    return (
        '<div class="table-wrap" tabindex="0" role="region" '
        f'aria-label="{escape(caption)}"><table class="comparison" id="{table_id}" '
        f'data-fixed-columns="{min(fixed_columns, len(cols) + 2)}">'
        f'<caption>{escape(caption)}</caption><colgroup>{colgroup}</colgroup>'
        f'<thead><tr>{header}</tr></thead><tbody>{"".join(rendered)}</tbody>'
        '</table></div>'
    )


def facts(items):
    return "".join(
        f'<li><strong>{escape(item["label"])}.</strong> {escape(item["text"])} '
        f'{sources(item.get("sources", []))}</li>'
        for item in items
    )


def render(data):
    main_cols = columns(data["columns"])
    if not main_cols or not data["rows"]:
        raise ValueError("At least one comparison column and candidate are required")
    rows = data["rows"]
    fixed_columns = data.get("fixed_columns", 2)
    if (isinstance(fixed_columns, bool) or not isinstance(fixed_columns, int)
            or not 2 <= fixed_columns <= len(main_cols) + 2):
        raise ValueError("fixed_columns must include rank/name and fit the table")
    pin_baseline = data.get("pin_baseline", True)
    if not isinstance(pin_baseline, bool):
        raise ValueError("pin_baseline must be boolean")
    ids = set()
    facets = data.get("facets", [])
    facet_ids = set()
    for facet in facets:
        key = identifier(facet["id"])
        if key in facet_ids:
            raise ValueError(f"Duplicate facet: {key}")
        facet_ids.add(key)
        columns(facet["columns"])
        if not facet["columns"]:
            raise ValueError(f"Facet needs a column: {key}")
    all_cols = {c["key"]: c for c in main_cols}
    for facet in facets:
        for column in facet["columns"]:
            if column["key"] in all_cols and column != all_cols[column["key"]]:
                raise ValueError(f'Conflicting column definition: {column["key"]}')
            all_cols[column["key"]] = column
    config_rows = []
    for order, row in enumerate(rows):
        key = identifier(row["id"])
        if key in ids:
            raise ValueError(f"Duplicate candidate: {key}")
        ids.add(key)
        if not isinstance(row["name"], str):
            raise ValueError(f"Candidate name must be text: {key}")
        if row.get("category", "candidate") not in {"candidate", "baseline", "excluded"}:
            raise ValueError(f"Invalid candidate category: {key}")
        if row.get("url"):
            url(row["url"])
        values, categories, present, terms = {}, {}, [], [row["name"]]
        for column_key, column in all_cols.items():
            value = cell(row, column_key)
            values[column_key] = value.get("value")
            categories[column_key] = value.get("category")
            terms.append(value["text"])
            if column.get("kind") == "feature" and value.get("present") is True:
                present.append(column_key)
        config_rows.append({"id": key, "order": order, "values": values,
                            "features": present, "categories": categories,
                            "baseline": row.get("category") == "baseline",
                            "search": " ".join(terms).lower()})
    filters = data.get("numeric_filters", [])
    controls = []
    for i, constraint in enumerate(filters):
        key = constraint["key"]
        if key not in all_cols or all_cols[key].get("kind") != "number":
            raise ValueError(f"Numeric filter needs a numeric column: {key}")
        options = '<option value="all">No limit</option>'
        for j, option in enumerate(constraint["options"]):
            number(option["max"])
            if "exclusive" in option and not isinstance(option["exclusive"], bool):
                raise ValueError("exclusive must be boolean")
            options += f'<option value="{j}">{escape(option["label"])}</option>'
        controls.append(f'<label>{escape(constraint["label"])}<select data-numeric="{i}">'
                        f'{options}</select></label>')
    categorical_filters = data.get("categorical_filters", [])
    category_controls = []
    for i, constraint in enumerate(categorical_filters):
        key = constraint["key"]
        if key not in all_cols:
            raise ValueError(f"Category filter needs a known column: {key}")
        options = '<option value="all">Any</option>'
        for j, option in enumerate(constraint["options"]):
            values = option["values"]
            if (not isinstance(values, list) or not values
                    or any(v is not None and (not isinstance(v, str) or not v) for v in values)):
                raise ValueError("Category options need a nonempty list of strings/null")
            options += f'<option value="{j}">{escape(option["label"])}</option>'
        category_controls.append(f'<label>{escape(constraint["label"])}'
                                 f'<select data-category="{i}">{options}</select></label>')
    feature_cols = [c for c in all_cols.values() if c.get("kind") == "feature"]
    feature_filter = ""
    if feature_cols:
        checks = "".join(f'<label class="feature-option"><input type="checkbox" '
                         f'value="{c["key"]}">{escape(c["label"])}</label>'
                         for c in feature_cols)
        feature_filter = ('<div class="feature-control"><span class="control-label">'
                          'Required features</span><details id="feature-menu" class="feature-menu">'
                          '<summary id="feature-summary">Any features</summary><fieldset id="feature">'
                          '<legend>Match all selected requirements</legend>' + checks + '</fieldset>'
                          '</details></div>')
    sort_options = '<option value="rank">My recommendation</option>'
    for c in all_cols.values():
        if c.get("kind") == "number":
            for direction, description in [("asc", "low to high"), ("desc", "high to low")]:
                sort_options += (f'<option value="{c["key"]}~{direction}">'
                                 f'{escape(c["label"])}, {description}</option>')
    table_id = identifier(data.get("table_id", "comparison-summary"))
    fragment_ids = {f'candidate-{row["id"]}' for row in rows if row.get("details")}
    fragment_ids.update(f'comparison-facet-{facet["id"]}' for facet in facets)
    if table_id in fragment_ids:
        raise ValueError(f"Summary table ID collides with another section: {table_id}")
    name_label = data.get("name_label", "Alternative")
    matrices = matrix(rows, main_cols, table_id, name_label, "Comparison summary",
                      fixed_columns, pin_baseline)
    for facet in facets:
        matrices += (f'<section class="facet"><h2>{escape(facet["title"])}</h2>'
                     + matrix(rows, facet["columns"], f'comparison-facet-{facet["id"]}',
                              name_label, facet["title"], fixed_columns, pin_baseline) + '</section>')
    details = ""
    for row in rows:
        if row.get("details"):
            title = escape(row["name"])
            if row.get("url"):
                title = f'<a href="{url(row["url"])}">{title}</a>'
            details += (f'<details class="candidate-detail" id="candidate-{row["id"]}" '
                        f'data-detail="{row["id"]}"><summary>{title}</summary>'
                        f'<ul class="notes">{facts(row["details"])}</ul>'
                        f'<a href="#{table_id}">Back to comparison</a></details>')
    picks = []
    row_map = {row["id"]: row for row in rows}
    for pick in data.get("picks", []):
        if pick["row_id"] not in row_map:
            raise ValueError(f'Unknown recommendation candidate: {pick["row_id"]}')
        row = row_map[pick["row_id"]]
        picks.append(f'<div class="pick"><small>{escape(pick["label"])}</small>'
                     f'<strong>{escape(row["name"])}</strong>'
                     f'<p>{escape(pick.get("summary", ""))}</p></div>')
    notes = data.get("notes", [])
    replacements = {
        "TITLE": escape(data["title"]), "SCOPE": escape(data["scope"]),
        "OBSERVED_AT": escape(data["observed_at"]),
        "PICKS": '<section class="picks">' + "".join(picks) + '</section>' if picks else "",
        "NUMERIC_FILTERS": "".join(controls),
        "CATEGORICAL_FILTERS": "".join(category_controls), "FEATURE_FILTER": feature_filter,
        "PIN_CONTROL": ('<label class="pin-control"><input id="pin-baseline" '
                        'type="checkbox"' + (' checked' if pin_baseline else '')
                        + '>Pin baseline</label><span class="meta">Pinned baseline ignores filters.</span>')
                       if any(row.get("category") == "baseline" for row in rows) else "",
        "SORT_OPTIONS": sort_options, "MATRICES": matrices, "DETAILS": details,
        "NOTES": '<details open><summary>Conditions and evidence</summary><ul class="notes">'
                 + facts(notes) + '</ul></details>' if notes else "",
        "CONFIG": json.dumps({"rows": config_rows, "numericFilters": filters, "pinBaseline": pin_baseline, "categoricalFilters": categorical_filters}, ensure_ascii=True)
                  .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
    }
    template = Path(__file__).resolve().parents[1] / "assets/report-template.html"
    text = template.read_text()
    # Substitute once so tokens inside untrusted text cannot become template markup.
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: replacements[m[1]], text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Comparison JSON; see references/data.md")
    parser.add_argument("output", type=Path, help="Durable standalone HTML destination")
    args = parser.parse_args()
    try:
        result = render(json.loads(args.input.read_text()))
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
