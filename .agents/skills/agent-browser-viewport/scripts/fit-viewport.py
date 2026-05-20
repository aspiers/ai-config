#!/usr/bin/env python3
"""Size the agent-browser window to fill its current screen, leaving
``bottom_margin`` device pixels free for the desktop panel.

Usage: fit-viewport.py [bottom_margin]   # default 50

Derives Chromium's chrome overhead from the current window's inner vs
outer dimensions, then issues one ``agent-browser set viewport`` call.
Verifies the result and corrects once if the initial overhead reading
disagreed with reality (rare — happens if inner dims were stale at
read time).
"""
import json
import subprocess
import sys

WIN_NAME = ".agent-browser-data"


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def screen_dims():
    info = json.loads(sh(["window-screen-info", "--json", "-n", WIN_NAME]))
    return info["screen"]["width"], info["screen"]["height"]


def window_metrics():
    out = sh(["agent-browser", "eval",
              "JSON.stringify({iw:innerWidth, ih:innerHeight, "
              "ow:outerWidth, oh:outerHeight, dpr:devicePixelRatio})"])
    for line in out.splitlines():
        line = line.strip().strip('"').replace('\\"', '"')
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"could not parse metrics from: {out!r}")


def overhead():
    m = window_metrics()
    return (round(m["ow"] - m["iw"] * m["dpr"]),
            round(m["oh"] - m["ih"] * m["dpr"]))


def main():
    bottom_margin = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    sw, sh_ = screen_dims()
    target_w, target_h = sw, sh_ - bottom_margin
    over_w, over_h = overhead()
    set_w, set_h = target_w - over_w, target_h - over_h
    print(f"screen {sw}x{sh_}, chrome overhead +{over_w}x+{over_h}, "
          f"setting viewport {set_w}x{set_h}")
    sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])

    new_over_w, new_over_h = overhead()
    if (new_over_w, new_over_h) != (over_w, over_h):
        set_w, set_h = target_w - new_over_w, target_h - new_over_h
        print(f"correcting: actual overhead +{new_over_w}x+{new_over_h}, "
              f"setting viewport {set_w}x{set_h}")
        sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])


if __name__ == "__main__":
    main()
