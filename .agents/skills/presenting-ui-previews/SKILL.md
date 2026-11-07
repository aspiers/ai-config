---
name: presenting-ui-previews
description: Builds a clickable before/after screenshot gallery of web UI work, at desktop and phone widths in light and dark, where clicking any screenshot opens the actual page it came from, with a full-length screenshot one link away. Use when showing the user screenshots or previews of UI changes for review, comparing pages before and after a change, or when screenshots handed over were cropped to the first screen. For a single image or page, open it directly as orca-cli-local or open-in-user-browser describes.
---

# Presenting UI previews

A reviewer of UI work wants to scan many views at once, then open the
actual page behind any of them. A gallery of first-screen thumbnails does
the first; clicking a screenshot must open the actual page it came from,
not a bigger picture, with a full-length screenshot one link away, so
nothing is judged from a crop.

## Build the gallery

[`scripts/ui-gallery.py`](scripts/ui-gallery.py) captures each page at each
width and colour scheme from an "after" server and, optionally, a "before"
one, and writes `index.html` plus one page per shot. Run it with
`--help` for its options. It needs Playwright with Chromium: use the
project's own Playwright environment where there is one, so no second
browser is downloaded.

Write the output into the project's scratch directory, not the system
`/tmp`, unless the project says otherwise.

By default it covers 1280 and 390 px, light and dark. Keep all four unless
the change cannot affect one of them: a layout change can break the phone
width, and a colour change the dark scheme. A "Show" selector at the top
of the index narrows it to one layout, such as phone width in dark, or to
one width or scheme.

## The "before" state

Serve the code from before the change on a second port, from a scratch
copy of the base ref (`git archive <ref> | tar -x -C <dir>`, then the
project's setup) or a worktree of it. Never stop or reuse a server or port
another agent or the user is using: pick a free port.

If the base ref can no longer be served, say so and present the after
shots alone rather than mixing in older screenshots taken another way.

## Signing in to a dev server

Pass `--login` with the path that starts a dev session. The script visits
it in the browser page, not through Playwright's request client: the
request client did not send a `Secure` session cookie back over plain
`http://127.0.0.1` (seen with Playwright 1.58), so a bootstrap request
loops between the sign-in page and the app. Each phase, width and scheme
gets its own browser context, so before and after sessions never collide.

## The actual page

Every screenshot, thumbnail or full-length, opens the actual page. By
default that is an MHTML snapshot the script saves for each phase and
page: the rendered page with its styles, which opens in any
Chromium-based browser, Orca's included, after the servers stop. Scripts
do not run in it, so only native controls such as `<details>` still
work. Where the project can export a page as one standalone HTML file
that keeps working, pass it with `--link`; it replaces the snapshot. Each
page also links the live URL, which works only while its server runs.

## Show it

Open `index.html` for the user in the same turn: in an Orca browser tab
inside Orca (`orca-cli-local`), otherwise with `open-in-user-browser`. Say
which branch or commit each phase shows and that the data is demo data
where it is.

## Third-party tools

`0xBrewing/ui-evidence` was audited and trialled on 2026-11-07 and not
adopted: it has no link to the real page, its thumbnails are whole pages
squashed to card size, and it needs Node, its own Chromium and a YAML
config. Check for anything newer before replacing this script.
