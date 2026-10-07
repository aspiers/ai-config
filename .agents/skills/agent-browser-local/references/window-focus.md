# Window-manager focus

On X11, agent-browser's headed Chromium can take keyboard focus from
whatever the user is typing in, so their next keystrokes land in the web
page. Fix it once in the window manager rather than per task.

## Why it happens

Chromium asks the window manager to activate its window with an EWMH
`_NET_ACTIVE_WINDOW` client message when agent-browser switches or opens a
tab: `tab <id>` sends `Page.bringToFront`, and `tab new` creates the target
in the foreground. A window manager that grants every such request hands
Chromium focus.

On agent-browser 0.38.2 with Chrome 153, `click`, `snapshot`, `get` and
`eval` left focus alone even with no protection, and no activation request
accompanied the click. An August 2026 run on an older,
unrecorded version saw a `click` move focus, so on other versions treat
clicks as suspect until measured.

Open upstream pull requests drop the implicit raise on tab switch and create
tabs in the background ([`#1695`][pr-1695], [`#1880`][pr-1880]; issue
[`#1247`][issue-1247]). Until one lands, and for anything else that raises
the window, the window manager has to refuse it.

[pr-1695]: https://github.com/vercel-labs/agent-browser/pull/1695
[pr-1880]: https://github.com/vercel-labs/agent-browser/pull/1880
[issue-1247]: https://github.com/vercel-labs/agent-browser/issues/1247

To confirm the path on another setup, watch the root window while running a
command:

```bash
xprop -root -spy _NET_ACTIVE_WINDOW
```

## General fix: refuse the agent window's activation requests

Tell the window manager to ignore activation requests from the agent-browser
window only. The user can still click into it by hand: clicks go through the
window manager's own button handling, not through `_NET_ACTIVE_WINDOW`.

Match the window by its `WM_CLASS` instance, which carries the profile
directory, e.g. `google-chrome (./.agent-browser-data)`. Read it with
`xprop WM_CLASS` and a click on the window.

### Fluxbox

Per-application `[FocusProtection]` refuses the requests:

```text
[app] (name=google-chrome.*agent-browser-data.*)
  [FocusProtection]	{Deny, Refuse}
[end]
```

`Deny` refuses the window's activation requests; `Refuse` stops a newly
mapped window taking focus.

**Availability:** `[FocusProtection]` is in Fluxbox master (commit
[`1a61881e`](https://github.com/fluxbox/fluxbox/commit/1a61881e), 2016) but
in no release; 1.3.7 does not parse it, so the rule is silently ignored.
Upstream master also skips it for windows re-managed by a Fluxbox restart,
because `Remember::setupFrame()` returns early on restart before applying
it.

> **⚠️ AUTHOR-SPECIFIC:** the author runs the openSUSE OBS package
> [`home:aspiers:branches:X11:windowmanagers/fluxbox`][obs-fluxbox]:
> 1.3.7 plus a backport of `[FocusProtection]` and a local patch that
> applies it on restart and adds a `SetFocusProtection` window command. Stock
> Fluxbox has neither.

[obs-fluxbox]: https://build.opensuse.org/package/show/home:aspiers:branches:X11:windowmanagers/fluxbox

A window that already existed before the rule was added keeps its old
protection. With the patched build, retrofit it without a restart:

```bash
fluxbox-remote "ForEach {SetFocusProtection Deny, Refuse} \
  {Matches (name=google-chrome.*agent-browser-data.*)}"
```

`fluxbox-remote` needs `session.screen0.allowRemoteActions: true`. Otherwise,
open a new agent-browser window, which picks up the rule when it maps. **Never
restart or kill the user's window manager to apply the rule** without their
explicit permission: restarts of the patched 1.3.7 have crashed it.

### Other window managers

Untested here. Look for focus-stealing prevention that applies to
`_NET_ACTIVE_WINDOW` requests, ideally per window, such as i3's
`focus_on_window_activation` or a KWin window rule. Wayland is untested.

## Verifying a fix

Ask the user first, since a failing test takes their focus. Sample the
active window around a tab switch to your own tab, in your own session (see
"Two agents" in [`SKILL.md`](../SKILL.md) for `$port` and `--pin-tab`):

```bash
before=$(xdotool getactivewindow)
agent-browser --session focustest --pin-tab --cdp "$port" tab "$my_tab"
sleep 1
after=$(xdotool getactivewindow)
[ "$before" = "$after" ] || xdotool windowactivate "$before"
```

## Without a window-manager fix

Before tab switches or new tabs (and clicks, on versions where they have
not been measured), warn the user to stop typing, or capture and restore
focus:

```bash
orig=$(xdotool getactivewindow)
# ... tab switches ...
xdotool windowactivate "$orig"
```

Do not swap native commands for JS `eval` writes to avoid focus; that needs
approval under the skill's native-commands rule.

## Evidence

- **2026-08-13, unprotected window, older agent-browser:** `click` on an
  inert `<div>` moved focus from the terminal to Chromium; `eval`,
  `snapshot` and `screenshot` did not. An earlier unannounced click put the
  fragment `"n the wrong"`, from the user's typing, into a Hubdoc amount
  field.
- **2026-10-06, unprotected window:** a tab switch took focus; `xprop`/`xev`
  on the root window showed Chromium sending `_NET_ACTIVE_WINDOW` and the
  window manager granting it, with the pointer elsewhere.
- **2026-10-06, Fluxbox `{Deny, Refuse}`:** a new window received 6
  activation requests during `window new`, a tab switch, `open` and a link
  `click`; all were refused and focus never moved.
- **2026-10-07, Fluxbox `{Deny, Refuse}`:** `tab new`, `click` (the button's
  handler ran), `fill`, `type`, and a link `click` that navigated all left
  `xdotool getactivewindow` unchanged; `_NET_ACTIVE_WINDOW` never changed.
- **2026-10-07, protection briefly set to `None`, agent-browser 0.38.2,
  Chrome 153:** `snapshot`, `get title`, `eval` and `click` on the visible
  tab kept focus, and `xev -root -event substructure` saw no
  `_NET_ACTIVE_WINDOW` from Chromium during the click. A tab switch straight
  after sent one and took focus.
- The restart fix and `SetFocusProtection` were verified on a private Xvfb
  display with a script that sends `_NET_ACTIVE_WINDOW` as an application.
