---
name: agent-browser-local
description: Applies local reliability, viewport, tab-safety, stale-ref, widget, and browser-boundary lessons to every agent-browser automation. Use alongside the upstream agent-browser skill whenever navigating, clicking, filling, testing, extracting, taking screenshots, or debugging any website with agent-browser.
---

# Local agent-browser guidance

Load the upstream `agent-browser` skill for its supported workflow, then apply
these cross-site rules. Application-specific skills may be stricter.

## Evidence provenance

- Viewport device-pixel behavior was empirically verified at DPR 1.5; the
  standalone helper documents and checks the calculation.
- Stale refs, `snapshot -i -C`, ExtJS containers, `dl` menus, bounded waits, and
  native-command preference were promoted from repeated Xero/Hubdoc automation
  findings rather than inferred from API shape.
- The no-op hit-test, page-only screenshot boundary, and regular-versus-agent
  browser distinction were directly reproduced on 2026-07-16.
- No `bd memories` entries currently exist; this skill promotes the durable
  evidence preserved in issue `ai-6rt` and the source skills.

## Reliable interaction loop

1. Inspect the active tab and take `snapshot -i -C` when hunting controls.
2. Scroll the target into view.
3. Take a fresh snapshot.
4. Click or fill the fresh ref immediately, with no intervening DOM action.
5. Re-snapshot after navigation, rerender, scrolling, or opening a widget.
6. Verify the resulting state; a dispatched click does not prove acceptance.

Ref ids such as `@e42` are ephemeral and may be reassigned after any update.

## Native commands first — JS writes need human approval

Use native subcommands (`get`, `find`, `scrollintoview`, `click`, `fill`,
`type`, `select`, `screenshot`) for every interaction. `eval` is for **reading
and diagnosis**, never a shortcut for driving the page.

**A write via `eval` (setting `.value`, dispatching events, calling `.click()`)
requires explicit human approval, for one of exactly two reasons:**

- **(a) Native is genuinely broken** — a bug or missing capability that **a
  human has confirmed**. Your own failed attempt is not confirmation.
- **(b) Native is too slow** and JS is materially faster — again, **approved by
  a human** first.

Absent (a) or (b), a native command that is not working means **you are calling
it wrong**. Read `agent-browser <cmd> --help` before concluding otherwise.

**Evidence (2026-08-13):** `agent-browser type "119.99"` appeared to do
nothing, twice. The signature is `type <selector> <text>` — the amount had been
passed as the *selector*, matching no element, while the CLI still printed
`✓ Done`. Instead of reading `--help`, the agent theorised that the framework
filtered synthetic events, then set every field by `eval` and left a
model-backed field uncommitted, blocking Publish. The correct native sequence
(`click` → `fill ""` → `type` → `click` away to blur) worked first time.

Two traps this exposes:

- **`✓ Done` means dispatched, not effective.** A wrong selector, a wrong
  argument order, and a genuine bug all print the same success line.
- **Application-specific skills may claim "always use JS" for a widget.** Treat
  that as a claim to re-test natively, not a licence. If native works, fix the
  skill.

When JS is approved, verify the result natively afterwards.

## Diagnose no-op clicks

Before theorising about application state, inspect the target rectangle and
hit-test its centre:

```js
const e = document.querySelector("SELECTOR");
const r = e.getBoundingClientRect();
({ r, viewport: [innerWidth, innerHeight], hit: document.elementFromPoint(
  r.left + r.width / 2, r.top + r.height / 2,
)?.outerHTML });
```

If the centre is off-screen or covered, run `scrollintoview`, snapshot again,
then click the new ref immediately.

**Evidence:** on 2026-07-16, two successful-looking Publish clicks were no-ops
because the button centre was below a 937-pixel viewport;
`elementFromPoint` returned `null`.

## Waiting

Avoid `wait --load networkidle` on applications with long polling, SSE,
telemetry, or persistent requests; they may never become idle. Wait for a
concrete selector/text/state when possible, otherwise use a bounded fixed wait.

## Viewport fitting

The default 1280×720 viewport is too short for many dense applications. Use the
separate [`agent-browser-viewport`](../agent-browser-viewport/SKILL.md) skill:

```bash
.agents/skills/agent-browser-viewport/scripts/fit-viewport.py
```

It accounts for Chromium chrome, device-pixel ratio, desktop-panel margin, and
the physical monitor. It takes effect without a reload. Rerun after moving the
window to another monitor.

**Design:** viewport fitting remains standalone because it has a focused
trigger and executable helper; this skill references it instead of duplicating
it.

## Shared-window tab safety

- Run `tab list` before assuming which page is active.
- Switch with `tab t<n>` (the `t` prefix is required; bare integers are
  rejected) rather than blindly opening another copy.
- Re-check `tab list` after focus jumps, new tabs, or external links.
- Tie evidence to the tab and browser instance from which it came.

### Two agents (or an agent and the user) in one browser

The active tab and the `@eN` ref table are **global to the agent-browser
session**, not per caller. Verified 2026-10-06 with two Claude sessions
sharing one Chrome:

- Another agent's `tab` switch between your `tab tX` and your `click @eN`
  sends your click to their page; a stray click landed on a Hubdoc icon this
  way.
- Another agent's `snapshot`, and even your own `tab tX`, invalidate refs:
  `Unknown ref: eN` straight after a fresh snapshot.
- Tabs can vanish (the user closes them) and new ones appear; a tab number
  says nothing about who opened it. Ask before using a tab you did not open.

Mitigations, best first:

1. **Separate sessions** attached to the running Chrome:

   ```bash
   port=$(agent-browser get cdp-url | sed -E 's#^ws://[^:]+:([0-9]+)/.*#\1#')
   agent-browser --session <name> --cdp "$port" tab new <url>
   ```

   Run `get cdp-url` in the session that launched Chrome (usually
   `default`), from the directory its profile is relative to. Always pass
   `--cdp`: `--session` alone launches a second Chrome on the same
   profile, which hands off to the running one and opens empty windows.

   Each session keeps its own refs and its own `tab` switches, but **any
   session's `tab new` moves every attached session's active tab** to the
   new tab (verified 2026-10-07). Run `tab list` after another agent may
   have opened a tab. Close your tabs with
   `curl -s http://127.0.0.1:$port/json/close/<target-id>` (ids from
   `/json/list`); `close` on an attached session only disconnects, leaving
   Chrome running.
2. Otherwise, put `tab tX` and the action **in one command chain**, and
   target elements by **CSS selector** (`#id`, `a:has(span.x)`,
   `dl:has(a[href*='…']) dt`) rather than `@eN` refs.
3. Message the other agent before a burst of browser actions and when done.

## Browser and profile boundaries

Agent-browser sees the page DOM and page viewport only. It cannot see or
operate native browser chrome: tab strip, address bar, permission prompts,
download shelf, or crash-recovery dialog. A 2026-07-16 verification screenshot
contained only the webpage, not the Chromium frame. Native UI requires an
explicitly approved OS/window-level tool.

**A freshly restarted agent-browser Chrome may be restorable: ask before
navigating.** Chrome offers its native "Restore pages" prompt only after an
abnormal exit (crash or kill, including `kill -9`; never after a clean
shutdown), so the prompt is proof the browser was killed and that session
state was saved. If `tab list` shows a lone `about:blank` where tabs used to
be, do **not** `open` a URL: that can discard the restorable session. Ask the
user whether a Restore prompt is showing and let them click it. A lone
`about:blank` is not proof the tabs are gone, and neither `snapshot` nor
`screenshot` can detect the prompt.

The boundary is crossed in the other direction too: on X11, `click`, tab
switches and `tab new` make Chromium ask the window manager for focus, and an
unconfigured one grants it, so the user's next keystrokes land in the page.
The general fix is a window-manager rule refusing the agent window's
activation requests; until one is in place, warn the user before such
commands or capture and restore focus. Read
[`references/window-focus.md`](references/window-focus.md) for the cause,
the Fluxbox rule, and how to verify a fix.

Agent-browser Chromium and the user's regular browser are separate processes
with separate profiles, ports, extensions, and sessions. Never use evidence
from one as proof about the other. The user's regular browser may itself
expose a remote-debugging port (e.g. 9222); that is never agent-browser's to
attach to, so don't theorise that agent-browser "failed to find" it.
Likewise, a fresh agent-browser Chrome that appears right after an `open` is
the aftermath of an earlier death, not its cause: diagnose crashes by
catching one as it happens and reading agent-browser's source, not by
reconstructing process history afterwards.

A relative profile such as `--user-data-dir=./.agent-browser-data` resolves
against the browser server's working directory. Changing that directory creates
a different profile and loses continuity despite identical relative path text.

## Generic widget patterns

### `dl` / `dt` / `dd` dropdowns

Some applications put the visible trigger in `<dt>` and a hidden menu in
`<dd>`. Do not hardcode generated ids. Snapshot and click the trigger ref first.
If native refs fail, locate the `<dl>` by visible label, force only its `<dd>`
visible, inspect it, and click the intended link:

```js
const menu = [...document.querySelectorAll("dl")].find((e) =>
  e.innerText.trim().startsWith("Options"),
);
const items = menu?.querySelector("dd");
Object.assign(items.style, {
  display: "block", visibility: "visible", opacity: "1",
});
items.innerHTML;
```

Re-query in the click operation rather than retaining a stale object.

### ExtJS autocomplete lists

ExtJS combo items may be bare static text with no snapshot ref.
`find text ... click` can hit a text node while the handler lives on the
`.x-combo-list-item` container.

1. Snapshot and click the field/cell ref.
2. Snapshot again and `type` the query; do not assume `fill` triggers the widget.
3. Wait briefly for the list.
4. Click the exact container, then snapshot to verify:

```js
[...document.querySelectorAll(".x-combo-list-item")]
  .find((e) => e.innerText.trim() === "EXACT LABEL")
  ?.click();
```
