# message-drop-sentinel: two findings from interactive trials

Environment: Claude Code v2.1.289, Opus 5.5 (high effort), Linux, run
interactively in Orca terminals with the sentinel's `hook.mjs` and
`relay.mjs` loaded via `--settings`.

## 1. PostToolBatch receipt races the transcript writer

**Symptom.** The receipt reports "0 plain-text message(s) persisted" for a
mid-turn text the user saw verbatim on screen, so the agent re-sends it and
the user gets duplicates.

**Cause.** PostToolBatch can fire before Claude Code appends the assistant
message that issued the batch. The hook scans the transcript too early.

**Evidence.** An instrumented copy logged the transcript size at hook fire
time and rescanned after 2 s:

| Runs | Text count at fire time | After 2 s |
| ---- | ----------------------- | --------- |
| 4/4  | 0                       | 1         |

In each case the file size at fire time ended exactly at the byte offset
where the heads-up text record was later written. Every heads-up was
visible on the user's screen.

**Fix.** The PostToolBatch payload carries `tool_calls[].tool_use_id`. Those
`tool_use` blocks follow the text in the same message, so the hook now polls
(50 ms interval, 3 s cap, fail-open) until every ID appears in the
transcript, then counts. With the fix, 3/3 runs counted the text correctly
after waits of 1-109 ms. A missing ID times out at 3 s and the hook falls
through to the old behaviour.

## 2. Mid-turn text can be shown as a summary and never persisted

In one turn the agent wrote a six-sentence paragraph between two tool
calls. The user's screen showed a different, one-line summary of it in its
place (wording the agent never wrote), and the transcript contains neither.
The receipt's "0" was correct about the transcript, but "LOST" overstates
it: the user saw a lossy version.

The hook cannot detect this, since it never sees what the screen rendered.
The only robust rule is the existing one: content that must be read
verbatim goes through the relay or the turn-final message.

Supporting evidence from session `9ffc97a1` (MANGO-4 trial):

- 2026-10-05, sentinel loaded: the one-line heads-up between two Bash
  calls showed verbatim. Its relay copy showed as `PostToolUse:Bash says:
  <text>` without Ctrl+O, and the receipt correctly counted 1. Both
  channels worked on a short line.
- 2026-10-16, same session resumed without the sentinel: a three-sentence
  paragraph written just before an AskUserQuestion call came out on screen
  reworded, with its first sentence dropped. The transcript holds no text
  block with the original. It holds the reworded version as a `thinking`
  block (record `d62be837`). One-line texts written before Bash calls in
  that same turn showed verbatim and were stored as `text` blocks.

So the agent's text reached the client as a summarised thinking block,
which Claude Code displayed and stored in its place. That explains why this
case leaves nothing for the hook to count.

Upstream already tracks this. anthropics/claude-code#102807 has a 13/13
repro in which a two-paragraph message between two tool calls comes back
as a `thinking` block. It links #65051, #75025, #76600, #76635 and #97504.
#95621 reports the same thing just before AskUserQuestion. Our extra data
point is that one-line messages between tool calls displayed verbatim both
times, so length may be a trigger. Not yet known: whether the API or
Claude Code does the reclassifying. Posted as
https://github.com/anthropics/claude-code/issues/102807#issuecomment-6251719906
on 2026-10-18.

Supporting evidence from a separate session (2026-10-08): an agent showed
the user a comment draft only through `cat` output and in prose written just
before an AskUserQuestion call. The user saw only "Read 1 file". Tool
results are collapsed by default, so tool output is not a delivery channel
either.

## Side note

The receipt is skipped on turns with no thinking blocks (by design). Opus
5.5 at high effort often skips thinking on simple turns, so agents in later
trial turns saw no receipts at all, were unsure whether to trust their
mid-turn text, and restated it anyway.

## Appendix: receipt race fix

The tested fix for finding 1, as patched into the sentinel's `hook.mjs`
(pinned at `cd940a4` of
[`podlayer/message-drop-sentinel`](https://github.com/podlayer/message-drop-sentinel)).
It runs at the top of the PostToolBatch handler, before the transcript scan:
`waitForBatchRecords(payload);`. The sentinel was not adopted, so this was
never submitted upstream.

```js
// PostToolBatch can fire before Claude Code has appended the assistant message
// that issued the batch, so a text written just before the tool call is not yet
// on disk and would be miscounted as lost. That message's tool_use blocks follow
// its text in the file, so once every tool_use_id in the payload is present, the
// text is too. Returns milliseconds waited, or -1 on timeout.
const BATCH_WAIT_MS = 3000;
function waitForBatchRecords(payload) {
  const ids = (payload.tool_calls ?? []).map((call) => call.tool_use_id).filter(Boolean);
  if (payload.hook_event_name !== 'PostToolBatch' || ids.length === 0) return 0;
  const start = Date.now();
  while (true) {
    const raw = fs.readFileSync(payload.transcript_path, 'utf8');
    if (ids.every((id) => raw.includes(`"type":"tool_use","id":"${id}"`))) return Date.now() - start;
    if (Date.now() - start >= BATCH_WAIT_MS) return -1;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 50);
  }
}
```
