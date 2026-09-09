#!/usr/bin/env python3

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

STAGES = {
    "local": (0, "⚪"),
    "published": (1, "🟡"),
    "draft": (2, "📝"),
    "blocked": (3, "🔴"),
    "ready": (4, "🟢"),
    "closed": (5, "⛔"),
    "merged": (6, "✅"),
}
REQUIRED_BRANCH_FIELDS = {
    "name",
    "purpose",
    "ahead",
    "behind",
    "stage",
    "progress",
    "next_step",
}


def escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_http_url(value: object) -> str | None:
    url = str(value)
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return escaped(url)
    return None


def linked_text(label: object, url: object | None) -> str:
    safe_url = safe_http_url(url) if url else None
    text = escaped(label)
    return f'<a href="{safe_url}">{text}</a>' if safe_url else text


def validate(data: object) -> dict:
    if not isinstance(data, dict):
        raise TypeError("report input must be a JSON object")

    required = {"repository", "upstream_ref", "as_of", "summary", "branches"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"missing report fields: {', '.join(sorted(missing))}")

    branches = data["branches"]
    if not isinstance(branches, list):
        raise TypeError("branches must be a JSON array")

    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            raise TypeError(f"branch {index} must be a JSON object")
        missing = REQUIRED_BRANCH_FIELDS - branch.keys()
        if missing:
            raise ValueError(
                f"branch {index} is missing fields: {', '.join(sorted(missing))}"
            )
        if branch["stage"] not in STAGES:
            choices = ", ".join(STAGES)
            raise ValueError(f"branch {index} stage must be one of: {choices}")
        for field in ("ahead", "behind"):
            if not isinstance(branch[field], int) or branch[field] < 0:
                raise ValueError(
                    f"branch {index} {field} must be a non-negative integer"
                )

    runtime_notes = data.get("runtime_notes", [])
    if not isinstance(runtime_notes, list):
        raise TypeError("runtime_notes must be a JSON array")
    return data


def render_rows(branches: list[dict]) -> str:
    rows = []
    ordered = sorted(branches, key=lambda branch: STAGES[branch["stage"]][0])
    for branch in ordered:
        stage = branch["stage"]
        emoji = STAGES[stage][1]
        purpose = f'<span class="purpose"> · {escaped(branch["purpose"])}</span>'
        request = branch.get("request")
        request_html = ""
        if isinstance(request, dict) and request.get("label"):
            request_html = linked_text(request["label"], request.get("url")) + " "
        rows.append(
            f'<tr class="stage-{stage}">'
            f"<td><code>{escaped(branch['name'])}</code>{purpose}</td>"
            f'<td class="divergence">↑{branch["ahead"]} ↓{branch["behind"]}</td>'
            f'<td class="progress"><span aria-hidden="true">{emoji}</span> '
            f"{request_html}{escaped(branch['progress'])}</td>"
            f"<td>{escaped(branch['next_step'])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_notes(notes: list[object]) -> str:
    if not notes:
        return ""
    items = "".join(f"<li>{escaped(note)}</li>" for note in notes)
    return f'<section class="notes"><h2>Other branches</h2><ul>{items}</ul></section>'


def render_report(data: dict, template: str) -> str:
    repository = escaped(data["repository"])
    canonical = data.get("canonical_url")
    repository_html = linked_text(data["repository"], canonical)
    freshness = (
        "Remote state was not refreshed."
        if data.get("stale")
        else "Remote state was refreshed."
    )
    replacements = {
        "{{TITLE}}": f"Upstreaming status: {repository}",
        "{{HEADING}}": f"Upstreaming status: {repository_html}",
        "{{SUMMARY}}": escaped(data["summary"]),
        "{{META}}": (
            f"Compared with <code>{escaped(data['upstream_ref'])}</code> · "
            f"{escaped(data['as_of'])} · {escaped(freshness)}"
        ),
        "{{ROWS}}": render_rows(data["branches"]),
        "{{EMPTY}}": ""
        if data["branches"]
        else '<p class="empty">No source branches qualify.</p>',
        "{{TABLE_HIDDEN}}": "" if data["branches"] else " hidden",
        "{{NOTES}}": render_notes(data.get("runtime_notes", [])),
    }
    markers = set(re.findall(r"\{\{[A-Z_]+\}\}", template))
    unknown = markers - replacements.keys()
    if unknown:
        raise ValueError(f"unknown template markers: {', '.join(sorted(unknown))}")
    return re.sub(
        r"\{\{[A-Z_]+\}\}",
        lambda match: replacements[match.group(0)],
        template,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an upstreaming-status HTML report"
    )
    parser.add_argument("--input", required=True, type=Path, help="JSON report data")
    parser.add_argument("--output", required=True, type=Path, help="HTML destination")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        data = validate(json.loads(args.input.read_text()))
        template_path = (
            Path(__file__).resolve().parent.parent / "assets" / "report.html"
        )
        output = render_report(data, template_path.read_text())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    except (OSError, TypeError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
