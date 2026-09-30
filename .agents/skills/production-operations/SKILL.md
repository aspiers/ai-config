---
name: production-operations
description: >-
  Puts the agent into a cautious production mode for live systems: read-only
  inspection may proceed, but credentials and out-of-scope personal data need
  permission first, every state-changing action needs explicit per-action
  approval with its resource risks and rollback stated, and anything
  unexpected halts work until the user decides. Use when the user invokes
  `/prod` or `$prod`, or says they are working on production, a live or
  customer-facing server, a mail server, or a production database, or asks
  for care on a system where mistakes affect real users.
---

# Production operations

Mistakes here affect real users and data, and may not be reversible. This
mode overrides the usual auto-mode latitude: an action being allowed by the
permission classifier or settings allowlist does **not** mean the user has
approved it. The rules below stay in force for the rest of the session
unless the user says otherwise.

## Read-only work: proceed, except for sensitive data

Inspecting state (status, logs, metrics, config, queue listings, `df`,
`free`, `ps`) may go ahead without asking, with two exceptions:

- **Credentials are always sensitive.** Ask before reading or printing
  private keys, passwords, tokens, API keys, or files likely to contain
  them, such as `.env` files or config with embedded secrets.
- **Personal data needs a clear mandate.** PII, email contents, mail logs,
  and other data covered by GDPR or similar law may be read only when the
  user's request clearly requires it. Investigating whether mail was lost
  after a mail server's disk filled up clearly covers reading mail logs and
  queued messages. If the need is not clear, ask first.

Prefer commands that show only what the question needs, such as headers or
counts rather than message bodies.

## State changes: explicit permission for every single one

Before **every** state-changing action, get the user's explicit permission.
There are no exceptions, and permission for one action does not carry over
to the next, even a near-identical one. Be most careful straight after a run
of read-only commands: momentum from steps that did not need approval is
exactly when an unapproved change slips through.

State-changing includes: moving, renaming, or deleting files (including
queue files); starting, stopping, restarting, or reloading services; editing
config; deleting, truncating, or rotating logs; requeuing, releasing, or
resending mail; database writes and migrations; package installs, upgrades,
and removals; cron and firewall changes. For anything else with side
effects, judge whether it changes the system or anything outside it, and ask
if in doubt.

When asking, use the questionnaire tool where available and state:

- the exact command(s) and what they change;
- the correctness risk: what could go wrong, and duplicate side effects such
  as mail sent twice or a job run twice;
- the **resource** risk: memory, disk, CPU, I/O, and connection limits, as
  checked on this host rather than assumed. For example, on a host with 2 GB
  RAM and no swap, requeuing one 28 MB message got Mailman's digest
  processing OOM-killed. Disk space and recipient bounces had been checked;
  memory had not;
- how to reverse the action or recover from it, and what cannot be undone.

## Keep changes minimal and reversible

Change only what the approved goal needs. Prefer moving files aside, for
example into a dated holding directory, over deleting them. Back up config
before editing it. Do one change at a time and check its effect before
proposing the next.

A command that changes state and then monitors the result must always print
its diagnostics, including when the monitoring times out or fails. Do not
let `set -e`, `&&` chains, or a `timeout` wrapper abort before status, logs,
or exit codes are shown; capture them unconditionally, for example in a
trap or a final block that always runs.

## When anything unexpected happens: stop

If an action you took, or a system you are changing, goes wrong or behaves
unexpectedly (a crash, an error, a partial result, a service going down,
output you cannot explain), stop at once. Do not investigate further, even
read-only, and do not try to fix it. First tell the user what happened,
what state the system is now in as far as you know, and what you have not
verified. Then ask how to proceed.

This does not cover odd but pre-existing state found during read-only
inspection, such as an unexplained file timestamp or a config change made
by someone else. Keep investigating that read-only, within the
sensitive-data limits above, and report it. Stop only if the finding
suggests something is actively going wrong, or the next step would change
state.
