---
name: triaging-prs
description: Scan every open pull request in a GitHub repository, filter to the ones that are genuinely mergeable now, and report a compact verdict with a suggested merge order. Use when the user asks which PRs can be merged, wants an open-PR backlog triaged or reviewed in bulk, asks why a PR is blocked, or wants to clear a queue of stale or bot-reviewed PRs.
---

# Triaging Open PRs for Mergeability

"Which of these can I merge right now?" is a filtering problem before it is a
review problem. A repo with twenty open PRs has maybe three worth reading,
and finding them by opening each one burns context on drafts and conflicts.

`scripts/pr-triage.sh` does the filtering. **Its output is a filter, not a
verdict** — it tells you which PRs are worth your attention, never which are
worth merging. That judgement is yours, and the rules below are where the
real work happens.

## Run the script

```bash
scripts/pr-triage.sh [-R owner/repo] [-l limit] [-a]
```

Defaults the repo from `$PWD`; `-h` prints usage. It emits the inventory of
every open PR, then — for the non-draft, conflict-free shortlist only — each
PR's non-passing checks and unresolved review threads (with who raised them
and whether they are outdated), and finally the branch ruleset that explains
why healthy PRs still say `BLOCKED`. Use `-a` to include drafts and
conflicted PRs in the per-PR pass.

One run answers the mechanical half of the question. Read the survivors'
diffs yourself.

## What the script is doing, and why

Read this when adapting the script, debugging odd output, or working a
surface it does not cover.

**The inventory is one call** — `gh pr list` requesting `number`, `title`,
`isDraft`, `mergeable`, `mergeStateStatus`, `additions`, `deletions` and
`changedFiles`, rendered through `column -t`. `--limit` defaults low in `gh`
itself, so the script passes 100; without it PRs silently vanish and you
triage a subset believing it is the whole set.

**Checks report only what is not passing**, so a clean PR costs one line
instead of twenty. `skipping` is excluded alongside `pass`: deploy-gated jobs
sit permanently skipped on PRs and are not failures. Never reach for
`gh pr checks --watch` here — on repos with permanently-skipping checks it
never exits. Poll snapshots instead.

**Unresolved threads need GraphQL.** Only `reviewThreads` exposes
`isResolved`; the REST review-comments endpoint carries no resolution state
at all. To act on those threads rather than count them, use the
`pr-comment-resolving` skill.

**The ruleset is queried once, not per PR.** It is a property of the branch,
and the blocker is normally identical across every PR. Note that
`gh api repos/OWNER/REPO/branches/main/protection` often reports "Branch not
protected" while a ruleset is actively enforcing — rulesets and legacy branch
protection are separate APIs, so a negative answer there proves nothing.

### Reading mergeStateStatus

| Status | Meaning |
|--------|---------|
| `BLOCKED` | Usually just "needs an approving review" — not a fault |
| `DIRTY` | Real merge conflicts with the base branch |
| `UNKNOWN` | GitHub is still computing mergeability, typically after another PR merged; re-poll in ~20s rather than reporting it |
| `CLEAN` | Nothing outstanding |

Treating `BLOCKED` as a problem is the most common triage error. It is the
normal resting state for a PR under a ruleset requiring approvals, which is
why the script keeps those PRs on the shortlist.

## Judgement, not just green lights

The script cannot decide any of this.

**Bot reviews are `COMMENTED`, never `APPROVED`.** A PR carrying a dozen
CodeRabbit or Copilot reviews still satisfies zero of a required-approval
rule. Do not read review volume as review coverage.

**A red e2e or deploy check is frequently infrastructure, not the code.**
Before reporting a failure, check whether the same check passes on the base
branch and on sibling PRs, and whether the PR even touches the failing
package. Deploy-gated e2e jobs fail when the preview deploy fails, so one
root cause commonly shows up as two red checks.

**Green CI plus no unresolved threads is not the same as reviewed.** This
distinction is the single most useful thing in the report: state plainly
which PRs you have read and which you have only measured.

**Read the diff before recommending a merge.** Mechanical green is a filter,
not a verdict. A PR can pass every automated check while its changeset
asserts something factually false about the product, or fixes two of the
three code paths it claims to fix.

**Check for overlapping files across the shortlist** and derive a merge
order from it:

```bash
gh pr view "$N" --json files --jq '.files[].path'
```

Whichever PR merges second will need a rebase; say so explicitly.

## Report format

Two tables and a merge order:

1. **Mergeable shortlist** — PR number, size, a one-line description of what
   the change actually does, and any caveat.
2. **Everything excluded** — each with its *one specific* blocker:
   `1 unresolved thread from @X, unanswered since 2026-07-28`; `coveralls
   failing`; `draft`. Never a vague "not ready" — a blocker the user cannot
   act on is not worth printing.

Then the suggested merge order with its reason, which is normally shared
files. Keep the reviewed/measured distinction visible in the shortlist table
rather than burying it in prose.

## Gotchas

- Piping `gh` output through `head` truncates mid-JSON and breaks any
  following `jq`. Write the full output to a file with `tee` and analyse the
  file (see the `slow-command-running` skill).
- Under `zsh` with `noclobber`, `>` silently fails when the target file
  exists, so a *stale* file gets analysed and the results look plausible.
  The script uses `mktemp` for exactly this reason; do the same in any
  ad-hoc command you add.
