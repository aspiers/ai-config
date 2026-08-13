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
Prefer native subcommands (`get`, `find`, `scrollintoview`, `click`, `fill`,
`type`, `select`, `screenshot`) over `eval`. Use JavaScript only when native
commands cannot operate the widget, then verify the result.

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

## Browser and profile boundaries

Agent-browser sees the page DOM and page viewport only. It cannot see or
operate native browser chrome: tab strip, address bar, permission prompts,
download shelf, or crash-recovery dialog. A 2026-07-16 verification screenshot
contained only the webpage, not the Chromium frame. Native UI requires an
explicitly approved OS/window-level tool.

The boundary is crossed in the other direction too: `click` raises and focuses
the Chromium window, stealing X focus from whatever the user is typing in, so
their next keystrokes land in the page. `eval`, `snapshot`, and `screenshot` do
not. Warn the user before a burst of clicks, or capture and restore focus
around it. See [`references/window-focus.md`](references/window-focus.md).

Agent-browser Chromium and the user's regular browser are separate processes
with separate profiles, ports, extensions, and sessions. Never use evidence
from one as proof about the other.

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
