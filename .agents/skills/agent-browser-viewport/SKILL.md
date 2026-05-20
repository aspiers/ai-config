---
name: agent-browser-viewport
description: Size the agent-browser Chromium window to fill its current screen, leaving a configurable bottom margin for the desktop panel. Use before any agent-browser automation that needs the full screen visible without elements overlapping or scrolling off (e.g. Xero, dense web apps).
---

# agent-browser viewport sizing

The default `agent-browser` viewport (1280x720) is too short for many
real-world web apps, causing elements to overlap or scroll unexpectedly.
This skill sizes the agent-browser Chromium window to fill its current
screen, leaving a configurable bottom margin for the desktop panel /
status bar.

## Usage

```bash
.agents/skills/agent-browser-viewport/scripts/fit-viewport.py        # default 50px bottom margin
.agents/skills/agent-browser-viewport/scripts/fit-viewport.py 80     # larger panel
```

Takes effect immediately on the current agent-browser session — no
reload needed. Run once before starting automation. Re-run if the
window has been moved to a different physical monitor.

## Why a script, not a fixed `-N` fudge

`agent-browser set viewport <w> <h>` sets the **outer** Chromium window
size, but Chromium then adds its tab strip + URL bar on top, so the
actual window ends up larger than the value you pass. The overhead
varies by Chromium version, theme, devicePixelRatio and window manager
— no fixed `-120` constant is reliable across machines.

## How the script works

It derives Chromium's chrome overhead directly from the existing window
state (no probe / resize loop, so the page layout isn't disturbed
mid-fit):

- horizontal overhead = `outerWidth - innerWidth × devicePixelRatio`
- vertical overhead = `outerHeight - innerHeight × devicePixelRatio`

`innerWidth` / `innerHeight` are CSS pixels; `outerWidth` /
`outerHeight` are device pixels. Multiplying inner by DPR brings them
into the same unit, and the difference is the chrome (tab strip + URL
bar + window border) in device pixels — exactly what `set viewport`
needs as its correction.

The script then:

1. Reads the screen the agent-browser window is currently on via
   `window-screen-info -n .agent-browser-data` (device pixels). Works
   correctly on multi-monitor setups.
2. Reads the in-page `innerWidth` / `innerHeight` / `outerWidth` /
   `outerHeight` / `devicePixelRatio` via `agent-browser eval`.
3. Computes overhead as above.
4. Issues one `agent-browser set viewport (screen_width - over_w,
   screen_height - bottom_margin - over_h)` call.

The final outer window matches `screen_width × (screen_height -
bottom_margin)` exactly (modulo half-pixel rounding at non-integer
DPR).

## Notes

- The script identifies the agent-browser window by its WM_CLASS
  instance `.agent-browser-data` — Chromium sets this from the
  `--user-data-dir` path that agent-browser passes.
- Reported screen dimensions are device pixels. `agent-browser set
  viewport` also takes device pixels, so values pass through directly.
  At `devicePixelRatio > 1` the in-page `innerWidth` / `innerHeight`
  will be smaller (CSS pixels = device pixels ÷ DPR), which is
  expected.
- If you need a different bottom margin (e.g. taller panel, multi-row
  taskbar), pass it as the first argument.
