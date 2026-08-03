---
name: watching-ci-runs
description: Watch a CI run's jobs to completion without idling or hand-writing a poll loop. Use when a dispatched or pushed build takes minutes to finish and its per-job results decide the next step.
---

# Watch CI Runs Without Waiting

Native builds routinely take 10-20 minutes. Blocking on them wastes that time,
and hand-rolled poll loops repeatedly get the same details wrong: emitting a
line per poll, staying silent on failure, or being launched twice for one run.

Arm one watcher, then keep working.

## Arm the watcher

Use the harness's event-stream monitor with the bundled script, which emits one
line per job as it reaches a terminal state and exits when the run completes:

```bash
scripts/watch-run.sh <run-id> [--interval SECONDS] [--repo OWNER/REPO]
```

Each job result arrives as its own notification, so a failure surfaces the
moment that job lands rather than when the whole run finishes. Set the monitor
timeout above the expected run duration; a matrix build needs far more than the
default.

## Keep working while it runs

The point of an event stream is that waiting costs nothing. After arming it,
start the next piece of work immediately. Never sleep, poll, or re-read the
output file to pass the time — a notification will arrive.

Good use of the interval: the next bead, a review of the diff just pushed,
documentation the change implies, or preparing the follow-up commit. Prefer
work that does not conflict with the commit under test, so a red result does not
invalidate it.

## One watcher per run

Before arming, check whether a watcher for that run already exists, and stop it
rather than adding a second. Two watchers on one run duplicate API calls and
split the results across output files, which is how a green job goes unnoticed.

If a result arrives from elsewhere before the watcher reports, that is not a
reason to start another watcher.

## Report every terminal state

Emit each job's actual conclusion, whatever it is. A watcher that matches only
success stays silent through a failure, and silence is indistinguishable from
still-running. Ask before arming: if this run failed right now, would anything
be emitted?

Tolerate transient API errors rather than dying or, worse, treating an empty
response as "nothing has finished" and re-announcing every job on recovery.

## Act on the result

Diagnose a failure from the logs already produced before dispatching anything
new; CI time is a finite paid budget. A single failed job does not justify
cancelling its siblings, whose independent results are often the faster
diagnosis.
