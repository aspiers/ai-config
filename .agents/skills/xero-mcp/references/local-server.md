# Local best-of-breed xero-mcp-server build

Upstream (XeroAPI/xero-mcp-server) merged nothing after 2026-06-05 and
has 70+ open PRs, so the MCP configs run a local build combining
reviewed PRs, maintained with the `git-branch-management` workflow.

## Layout

- Checkout: `~/.GIT/3rd-party/xero-mcp-server`. Remotes: `origin` =
  XeroAPI (upstream), `github` = aspiers fork.
- PR heads are fetched as `origin/pr/<N>`; each included PR has a local
  branch `pr/<N>` tracking it.
- The main checkout has `working` checked out — the mixdown of every
  source branch. `.mcp.json` / `opencode.json` run its `dist/index.js`,
  so **rebuilding the main checkout changes the live server** (after an
  agent restart).
- Branch tree: `git machete status` (layout in `.git/machete`). Mix
  membership: `ggmx working`.
- Local branches, each in a `wt` worktree under `.worktrees/`:
  - `xero-node-20` — xero-node v20 upgrade (upstream PR #314)
  - `pr/187-v20`, `pr/296-v20` — PRs rebased onto v20 with compat fixes
  - `pr/200-fixes` — cross-process refresh locking and hardening on
    top of #200
  - `pr/109-no-client` — #109 minus its stale `xero-client.ts` hunk
  - `pr/110+289`, `pr/296+216` — integration merges for PR pairs
    whose combination needs edits outside conflicting files

## Why some PRs are excluded

Reviewed 2026-09-23 (diffs read for secret handling, network calls,
dependency changes and data-corruption risk):

- **FAIL:** #295 (a partial line update wipes the other invoice lines),
  #126 (renames the package, stale client rewrite).
- **Superseded duplicates:** #180 (inside #181), #197 (#190 keeps
  `lineAmountTypes`), #215 (#214), #313/#204/#178 (#207), #198/#161
  (#186), #201 (bundle; #296 taken for currency).
- **Out of scope:** AU payroll (#166–#171, #202, #299, #304), quotes,
  remote hosting (#101, #135, #310).

Write-capable tools included by choice, with no confirmation step:
invoice status changes (#221), linked-transaction delete/void (#191),
permanent history notes (#145), credit-note allocation delete (#194),
re-dating authorised credit notes (#195 — keep a Xero lock date set).

## Rebuilding after any source-branch change

A source branch changes when you commit to it, or when its PR gets new
commits (`git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'`
then fast-forward `pr/<N>`). Then, in the main checkout:

```bash
ggmxd -s recursive -c                   # rebuild `working` from all sources
npm ci && npm run build && npx vitest run && npm run lint
```

and restart the agent sessions to load the new build.

`rerere` is enabled and replays every recorded conflict resolution;
`git-mixdown` commits a merge automatically when rerere resolved all
of it, and aborts (listing the files) when a conflict is new. Then
resolve the files, `git add`, and commit with
`AS_GIT_ALLOW_WORKING_COMMIT=1 git commit --no-edit` so rerere records
the resolution, and re-run the mixdown.

**rerere only replays files that textually conflicted.** If a
combination needs an edit to any other file (typically a test asserting
an old call shape), do not commit it on `working` — it would be lost on
the next mixdown. Put it on an integration branch instead: a `wt`
worktree off one PR, merge the other PR in, commit the fix, record it
in `.git/machete`, and replace both PRs in the mix with it (as
`pr/110+289` does).

Never develop on `working` or push it.

## Adding another upstream PR

1. Review its diff (secrets, network, dependencies, data risk) before it
   ever runs against live books.
2. `git branch --track pr/<N> origin/pr/<N>`, add it to
   `.git/machete` and `ggmx working +pr/<N>`.
3. Check it against v20: `npx tsc --noEmit` after the mixdown catches
   any positional-argument shifts (see below).
4. Rebuild as above.

## xero-node v20 positional-argument shifts

v20 inserted new optional parameters before the trailing `options`
argument of `createInvoices` / `updateInvoice` / `updateOrCreateInvoices`
(`allowBackorders`), `getBankTransactions` / `getOverpayments`
(`references`), `getPrepayments` (`invoiceNumbers`, `references`) and
`getBankTransfers` (`includeDeleted`). Code written against v13 passes
the client headers into the new slot; `tsc` flags it, and the fix is an
explicit `undefined` per new parameter.
