# Window-manager focus

`agent-browser click` raises and focuses the agent-browser Chromium window,
taking X focus away from the user's terminal. Anything they type next goes
into the web page.

## Which commands steal focus

Verified 2026-08-13 by sampling `xdotool getactivewindow` either side of each
command, clicking an inert `<div>` so nothing else could interfere:

| Command      | Steals focus |
|--------------|--------------|
| `click`      | **yes**      |
| `eval`       | no           |
| `snapshot`   | no           |
| `screenshot` | no           |

Untested: `fill`, `type`, `select`, `scrollintoview`, `navigate`. Assume any
command that drives the page may behave like `click` until shown otherwise.

Verified on this machine's X session only. Wayland and other window managers
are untested.

## Working safely

Prefer the focus-safe commands when they can do the job. JS via `eval` reads
and writes the DOM without touching the window, which is why a pure-`eval`
field-setting pass causes no interference.

When clicks are unavoidable, either tell the user you are about to take focus
(so they hold off typing), or capture and restore it:

```bash
ORIG=$(xdotool getactivewindow)
# ... clicks ...
xdotool windowactivate "$ORIG"
```

## Evidence

On 2026-08-13 a click on Hubdoc's `#edit-data-total-container` moved focus
from `herdr-git` (id 54525966) to `Hubdoc - Google Chrome` (id 77594628).

Earlier in the same session an unannounced click during the user's typing put
the fragment `"n the wrong"` — mid-sentence text from their message — into
Hubdoc's Total Amount field, which then had to be cleared. The field was
mid-diagnosis at the time, so the stray text was briefly misread as a tool
malfunction.

That misreading is its own lesson: the user reported only that focus had
moved "while you were working on it". Attributing it to `click` specifically
was a guess until the `xdotool` test above was run. Do not write an untested
cause into a skill; run the cheap experiment or record the uncertainty.
