#!/usr/bin/env python3
"""Size the agent-browser window to fill its current screen, leaving
``bottom_margin`` CSS pixels free for the desktop panel.

Usage: fit-viewport.py [bottom_margin]   # default 50

``agent-browser set viewport W H`` consumes **CSS pixels** — the
browser's own coordinate space — so all arithmetic here is done in CSS
pixels too. The available screen size is read from the browser's own
``window.screen.availWidth`` / ``availHeight`` (also CSS px), NOT from
the X11 ``window-screen-info`` device-pixel size.

This matters on displays with fractional X11 scaling: there the X11
device-pixel screen size is ~1.33x larger than the CSS-pixel screen
size, yet ``window.devicePixelRatio`` reports 1.0 and does NOT capture
that scaling. Feeding device pixels to ``set viewport`` would overshoot
by the scaling factor, so we deliberately avoid them.

Chromium's chrome overhead is derived from the current window's inner
vs outer dimensions (plain CSS px subtraction). One ``set viewport``
call is issued; the result is verified and corrected once if the
initial overhead reading disagreed with reality (overhead can vary a
few px between reads).
"""
import json
import subprocess
import sys


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def window_metrics():
    out = sh(["agent-browser", "eval",
              "JSON.stringify({iw:innerWidth, ih:innerHeight, "
              "ow:outerWidth, oh:outerHeight, "
              "aw:screen.availWidth, ah:screen.availHeight})"])
    for line in out.splitlines():
        line = line.strip().strip('"').replace('\\"', '"')
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"could not parse metrics from: {out!r}")


def main():
    bottom_margin = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    m = window_metrics()
    avail_w, avail_h = m["aw"], m["ah"]
    over_w, over_h = m["ow"] - m["iw"], m["oh"] - m["ih"]
    target_w, target_h = avail_w, avail_h - bottom_margin
    set_w, set_h = target_w - over_w, target_h - over_h
    print(f"avail {avail_w}x{avail_h}, chrome overhead +{over_w}x+{over_h}, "
          f"setting viewport {set_w}x{set_h}")
    sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])

    m = window_metrics()
    new_over_w, new_over_h = m["ow"] - m["iw"], m["oh"] - m["ih"]
    if (new_over_w, new_over_h) != (over_w, over_h):
        set_w, set_h = target_w - new_over_w, target_h - new_over_h
        print(f"correcting: actual overhead +{new_over_w}x+{new_over_h}, "
              f"setting viewport {set_w}x{set_h}")
        sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])


if __name__ == "__main__":
    main()
