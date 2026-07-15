#!/usr/bin/env python3
"""Size the agent-browser window to fill its current screen, leaving
``bottom_margin`` CSS pixels free for the desktop panel.

Usage: fit-viewport.py [bottom_margin]   # default 50

``agent-browser set viewport W H`` consumes **device pixels** — verified
empirically: on a DPR=1.5 display, ``set viewport 1500 1000`` produced
``innerWidth == 1000`` (= 1500 / 1.5), i.e. the value passed sets the
*device-pixel* inner size, not the CSS-pixel one. So all arithmetic here
is done in device pixels.

**Which readings are which unit:** in the browser ``window`` object,
``outerWidth`` / ``outerHeight`` and ``screen.availWidth`` /
``availHeight`` are already **device pixels**; only ``innerWidth`` /
``innerHeight`` are **CSS pixels**. To keep everything in device px we
multiply the inner dimensions by ``devicePixelRatio`` when computing the
chrome overhead:

- target outer size (device px) = ``screen.availWidth`` (minus bottom
  margin on the height)
- chrome overhead   (device px) = ``outerWidth - innerWidth * dpr``
- viewport to set   (device px) = target outer - overhead

The earlier revision assumed ``set viewport`` took CSS px and that
``screen.availWidth`` was CSS px; both are false on DPR != 1 displays,
which left the window filling only ~66% of the screen.

One ``set viewport`` call is issued; the result is verified and
corrected once if the initial overhead reading disagreed with reality
(overhead can vary a few px between reads).
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
              "aw:screen.availWidth, ah:screen.availHeight, "
              "dpr:devicePixelRatio})"])
    for line in out.splitlines():
        line = line.strip().strip('"').replace('\\"', '"')
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"could not parse metrics from: {out!r}")


def main():
    bottom_margin = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Everything below is in device pixels. outerWidth/Height and
    # screen.availWidth/Height are already device px; innerWidth/Height
    # are CSS px, so multiply them by dpr to reach device px when
    # computing the chrome overhead (see module docstring).
    def device_metrics():
        m = window_metrics()
        dpr = m["dpr"]
        return {
            "avail_w": m["aw"],
            "avail_h": m["ah"],
            "over_w": m["ow"] - m["iw"] * dpr,
            "over_h": m["oh"] - m["ih"] * dpr,
        }

    d = device_metrics()
    target_w, target_h = d["avail_w"], d["avail_h"] - bottom_margin
    set_w, set_h = round(target_w - d["over_w"]), round(target_h - d["over_h"])
    print(f"avail {d['avail_w']}x{d['avail_h']} device px, "
          f"chrome overhead +{round(d['over_w'])}x+{round(d['over_h'])}, "
          f"setting viewport {set_w}x{set_h}")
    sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])

    d2 = device_metrics()
    if (round(d2["over_w"]), round(d2["over_h"])) != (round(d["over_w"]), round(d["over_h"])):
        set_w, set_h = round(target_w - d2["over_w"]), round(target_h - d2["over_h"])
        print(f"correcting: actual overhead "
              f"+{round(d2['over_w'])}x+{round(d2['over_h'])}, "
              f"setting viewport {set_w}x{set_h}")
        sh(["agent-browser", "set", "viewport", str(set_w), str(set_h)])


if __name__ == "__main__":
    main()
