#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
"""Build a before/after screenshot gallery of web pages for review.

For every phase (before, after), page, width and colour scheme it saves a
first-screen PNG, a full-page PNG and an HTML page showing the full-length
shot at real size. For every phase and page it saves the actual page as an
MHTML snapshot that opens without the server. index.html shows first-screen
thumbnails: each opens the actual page, with a link to its full-length shot.

Run it with a Python that has Playwright and its Chromium, such as the
project's own environment, or `uv run ui-gallery.py ...` and then
`playwright install chromium` if the browser is missing.
"""

import argparse
import html
import shutil
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

PHONE_MAX = 480


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--after", required=True, metavar="URL", help="base URL of the server showing the change")
    parser.add_argument("--before", metavar="URL", help="base URL of a server running the code before the change")
    parser.add_argument(
        "--page",
        action="append",
        required=True,
        metavar="ID|LABEL|PATH",
        help='page to capture, e.g. "draft|Draft report|/reports/7"; repeat for more',
    )
    parser.add_argument("--width", action="append", type=int, metavar="PX", help="viewport width; default 1280 and 390")
    parser.add_argument(
        "--scheme",
        action="append",
        choices=["light", "dark"],
        help="colour scheme; default both",
    )
    parser.add_argument(
        "--login",
        metavar="PATH",
        help="path the browser visits first on each server to get a session, e.g. /auth/login",
    )
    parser.add_argument("--wait", metavar="SELECTOR", help="CSS selector that shows the page has rendered")
    parser.add_argument(
        "--link",
        action="append",
        default=[],
        metavar="[PHASE:]ID=TARGET",
        help="the actual page to open instead of the MHTML snapshot: a URL, or a standalone HTML file "
        "(copied into the gallery); PHASE defaults to after",
    )
    parser.add_argument("--title", default="UI preview", help="gallery heading")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    return parser.parse_args()


def parse_pages(specs: list[str]) -> list[tuple[str, str, str]]:
    pages = []
    for spec in specs:
        parts = spec.split("|")
        if len(parts) != 3 or not all(parts):
            sys.exit(f'--page needs "ID|LABEL|PATH", got {spec!r}')
        pages.append(tuple(parts))
    return pages


def parse_links(specs: list[str], out: Path) -> dict[tuple[str, str], str]:
    """Map (phase, page id) to an href, copying local files into the gallery."""
    links = {}
    for spec in specs:
        key, sep, target = spec.partition("=")
        if not sep or not target:
            sys.exit(f"--link needs [PHASE:]ID=TARGET, got {spec!r}")
        phase, _, page_id = key.rpartition(":")
        phase = phase or "after"
        source = Path(target)
        if source.is_file():
            name = f"{phase}-{page_id}-standalone{source.suffix}"
            shutil.copyfile(source, out / name)
            target = name
        links[(phase, page_id)] = target
    return links


DARK = """color-scheme:dark;--bg:#0f1318;--bg-top:#141a21;--panel:#171d25;--soft:#1d2530;--ink:#e7ecf2;
--muted:#9aa6b5;--line:rgba(220,230,245,.13);--accent:#86adff;--danger:#ff8a80;--shadow:rgba(0,0,0,.4)"""

# The viewer's choice (data-theme) wins over the system setting; "system" removes the attribute.
STYLE = f"""<style>
:root{{color-scheme:light;--bg:#f2f4f8;--bg-top:#f9fafc;--panel:#fff;--soft:#f5f7fa;--ink:#18202b;
--muted:#5b6676;--line:rgba(23,32,48,.12);--accent:#2457c5;--danger:#b42318;--shadow:rgba(16,24,40,.07)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{{DARK}}}}}
:root[data-theme=dark]{{{DARK}}}
*{{box-sizing:border-box}}
.topbar{{display:flex;justify-content:flex-end;margin-bottom:12px}}
.theme{{display:inline-flex;padding:3px;gap:2px;border-radius:999px;background:var(--panel);
border:1px solid var(--line);box-shadow:0 6px 18px var(--shadow)}}
.theme button{{font:inherit;font-size:.85rem;color:var(--muted);background:none;border:0;border-radius:999px;
padding:4px 12px;cursor:pointer}}.theme button[aria-pressed=true]{{background:var(--accent);color:var(--panel)}}
.theme button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}"""
STYLE += """
body{margin:0;background:linear-gradient(180deg,var(--bg-top),var(--bg));color:var(--ink);
font:15px/1.6 "Avenir Next","Segoe UI",system-ui,sans-serif}
main{width:min(1360px,calc(100% - 28px));margin:18px auto 48px}
h1,h2{font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-weight:600;line-height:1.15}
h1{font-size:clamp(1.8rem,4vw,2.6rem);margin:.2rem 0 .4rem}h2{font-size:1.6rem;margin:0 0 .3rem}
h3{font-size:1rem;margin:0}a{color:var(--accent)}.muted{color:var(--muted)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:20px;
box-shadow:0 14px 40px var(--shadow)}.panel+.panel{margin-top:16px}
.pills{display:flex;flex-wrap:wrap;gap:10px;margin:.6rem 0}
.pill{display:inline-flex;align-items:center;gap:8px;min-height:34px;padding:0 12px;border-radius:999px;
background:var(--soft);border:1px solid var(--line);color:var(--muted);font-size:.9rem}
.pill strong{color:var(--ink)}.pill.danger,.pill.danger strong{color:var(--danger)}
.filter{position:sticky;top:8px;z-index:1;margin:16px 0}.filter .pill{box-shadow:0 6px 18px var(--shadow)}
.filter select{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--line);
border-radius:999px;padding:2px 10px}
.row{display:grid;grid-template-columns:repeat(var(--phases),minmax(0,1fr));gap:14px;align-items:start;
margin-top:18px}.row[hidden]{display:none}.row h3{grid-column:1/-1}
figure{margin:0;padding:12px;background:var(--soft);border:1px solid var(--line);border-radius:16px}
figcaption{font-size:.78rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
margin-bottom:8px}
.thumb{display:block}.thumb img{display:block;max-width:100%;border:1px solid var(--line);border-radius:10px;
background:#fff}.phone .thumb img{max-width:min(100%,390px)}
a:hover img,a:focus-visible img{outline:3px solid var(--accent);outline-offset:2px}
figure .thumb+a{display:inline-block;margin-top:8px;font-size:.9rem}
.shot{overflow-x:auto}.shot img{display:block;max-width:none;border-radius:10px}
.failed{color:var(--danger);margin:0}
</style>"""

# Applies the saved theme before the page paints, so it never flashes the other theme.
THEME_HEAD = """<script>
try {
  const theme = localStorage.getItem("ui-gallery-theme");
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
} catch {}
</script>"""

THEME_TOGGLE = (
    '<div class="topbar"><div class="theme" role="group" aria-label="Colour theme">'
    + "".join(f'<button type="button" data-choice="{c.lower()}">{c}</button>' for c in ("Light", "Dark", "System"))
    + "</div></div>"
)

THEME_SCRIPT = """<script>
const themeButtons = document.querySelectorAll(".theme button");
function markTheme() {
  const current = document.documentElement.dataset.theme || "system";
  for (const button of themeButtons) button.setAttribute("aria-pressed", button.dataset.choice === current);
}
for (const button of themeButtons) {
  button.addEventListener("click", () => {
    const choice = button.dataset.choice;
    if (choice === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = choice;
    try { localStorage.setItem("ui-gallery-theme", choice); } catch {}
    markTheme();
  });
}
markTheme();
</script>"""

# Hides the rows whose width and scheme don't match the chosen view; remembers the choice per viewer.
FILTER_SCRIPT = """<script>
const pick = document.getElementById("view");
function show(view) {
  const wanted = view.split(" ").filter(Boolean);
  for (const row of document.querySelectorAll(".row")) {
    const tags = row.dataset.view.split(" ");
    row.hidden = !wanted.every((tag) => tags.includes(tag));
  }
}
let saved = "";
try { saved = localStorage.getItem("ui-gallery-view") || ""; } catch {}
if ([...pick.options].some((option) => option.value === saved)) pick.value = saved;
show(pick.value);
pick.addEventListener("change", () => {
  show(pick.value);
  try { localStorage.setItem("ui-gallery-view", pick.value); } catch {}
});
</script>"""


def layout_name(width: int) -> str:
    return f"{'Phone' if width <= PHONE_MAX else 'Desktop'} {width} px"


def view_filter(widths: list[int], schemes: list[str]) -> str:
    options = [("", "All layouts")]
    if len(schemes) > 1:
        options += [(str(width), f"{layout_name(width)}, all schemes") for width in widths]
    if len(widths) > 1:
        options += [(scheme, f"All widths, {scheme}") for scheme in schemes]
    if len(widths) > 1 or len(schemes) > 1:
        options += [(f"{w} {s}", f"{layout_name(w)}, {s}") for w in widths for s in schemes]
    choices = "".join(f'<option value="{value}">{html.escape(text)}</option>' for value, text in options)
    return f'<div class="filter"><label class="pill">Show <select id="view">{choices}</select></label></div>'


def document(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>{THEME_HEAD}{STYLE}</head><body><main>"
        f"{THEME_TOGGLE}{body}</main>{THEME_SCRIPT}</body></html>"
    )


def real_links(actual: str, live: str, which: str = "") -> str:
    return (
        f'<a href="{html.escape(actual)}">Open the actual {which}page</a> · '
        f'<a href="{html.escape(live)}">live {which}page (while its server runs)</a>'
    )


def capture(page, base: str, path: str, login: str | None, wait: str | None, stem: Path, snapshot: Path) -> None:
    if login:
        page.goto(base + login)
    page.goto(base + path)
    if wait:
        page.locator(wait).first.wait_for()
    else:
        page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    page.screenshot(path=f"{stem}-top.png")
    page.screenshot(path=f"{stem}-full.png", full_page=True)
    if not snapshot.exists():
        # MHTML keeps the rendered page with its styles, so it opens after the server stops.
        cdp = page.context.new_cdp_session(page)
        snapshot.write_text(cdp.send("Page.captureSnapshot", {"format": "mhtml"})["data"], "utf-8")
        cdp.detach()


def main() -> int:
    args = parse_args()
    pages = parse_pages(args.page)
    widths = args.width or [1280, 390]
    schemes = args.scheme or ["light", "dark"]
    phases = [(name, url.rstrip("/")) for name, url in (("before", args.before), ("after", args.after)) if url]
    args.out.mkdir(parents=True, exist_ok=True)
    links = parse_links(args.link, args.out)
    cells: dict[tuple[str, str, int, str], str] = {}
    failures = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for phase, base in phases:
            for width in widths:
                for scheme in schemes:
                    # One context per combination: sessions stay apart even when servers share a host.
                    context = browser.new_context(
                        viewport={"width": width, "height": 844 if width <= PHONE_MAX else 800},
                        color_scheme=scheme,
                    )
                    page = context.new_page()
                    for page_id, label, path in pages:
                        name = f"{phase}-{page_id}-{width}-{scheme}"
                        title = f"{label}: {phase}, {width} px, {scheme}"
                        live = base + path
                        actual = links.get((phase, page_id), f"{phase}-{page_id}.mhtml")
                        try:
                            snapshot = args.out / f"{phase}-{page_id}.mhtml"
                            capture(page, base, path, args.login, args.wait, args.out / name, snapshot)
                        except PlaywrightError as error:  # report every failed shot, keep the rest
                            failures += 1
                            message = f"{title}: {str(error).splitlines()[0]}"
                            print(f"failed: {message}", file=sys.stderr)
                            cells[(phase, page_id, width, scheme)] = (
                                f'<p class="failed">Failed: {html.escape(message)}</p>'
                            )
                            continue
                        (args.out / f"{name}.html").write_text(
                            document(
                                title,
                                f'<header class="panel"><p><a href="index.html">Back to all screenshots</a> · '
                                f"{real_links(actual, live)}</p>"
                                f'<h1>{html.escape(title)}</h1><p class="muted">Full-length screenshot. '
                                "Click it to open the actual page.</p></header>"
                                f'<div class="panel shot"><a href="{html.escape(actual)}"><img src="{name}-full.png" '
                                f'alt="{html.escape(title)}, full length"></a></div>',
                            ),
                            "utf-8",
                        )
                        cells[(phase, page_id, width, scheme)] = (
                            f'<a class="thumb" href="{html.escape(actual)}"><img src="{name}-top.png" '
                            f'alt="{html.escape(title)}, first screen; opens the actual page"></a>'
                            f'<a href="{name}.html">Full-length screenshot</a>'
                        )
                    context.close()
        browser.close()

    sections = []
    for page_id, label, path in pages:
        rows = []
        for width in widths:
            for scheme in schemes:
                figures = "".join(
                    f"<figure><figcaption>{phase.capitalize()}</figcaption>"
                    f"{cells[(phase, page_id, width, scheme)]}</figure>"
                    for phase, _ in phases
                )
                size = "phone" if width <= PHONE_MAX else "desktop"
                rows.append(
                    f'<div class="row {size}" data-view="{width} {scheme}" style="--phases:{len(phases)}">'
                    f"<h3>{layout_name(width)}, {scheme}</h3>{figures}</div>"
                )
        page_links = " · ".join(
            real_links(links.get((phase, page_id), f"{phase}-{page_id}.mhtml"), base + path, f"{phase} ")
            for phase, base in phases
        )
        sections.append(
            f'<section class="panel"><h2>{html.escape(label)}</h2><p>{page_links}</p>{"".join(rows)}</section>'
        )

    now = datetime.now().astimezone()
    shots = len(cells) - failures
    failed_tone = " danger" if failures else ""
    summary = (
        f'<div class="pills"><span class="pill"><strong>{shots}</strong> screenshots</span>'
        f'<span class="pill{failed_tone}"><strong>{failures}</strong> failed</span>'
        f'<span class="pill"><strong>{" and ".join(p for p, _ in phases)}</strong></span>'
        f'<span class="pill">generated <strong>{now.day} {now:%b %Y, %H:%M}</strong></span></div>'
    )
    index = args.out / "index.html"
    index.write_text(
        document(
            args.title,
            f'<header class="panel"><h1>{html.escape(args.title)}</h1>{summary}'
            '<p class="muted">Each picture is the first screen of a page: click it to open the actual page, '
            "or use the link under it for a full-length screenshot.</p></header>"
            + view_filter(widths, schemes)
            + "".join(sections)
            + FILTER_SCRIPT,
        ),
        "utf-8",
    )
    print(index.resolve())
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
