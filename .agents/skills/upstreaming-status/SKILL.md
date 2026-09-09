---
name: upstreaming-status
description: >-
  Reports how local Git branches are progressing toward canonical upstream
  inclusion as a browser-rendered HTML report with branch purpose, ahead/behind
  counts, pull-request or merge-request status, and next action.
  Use when asked for upstreaming status, local branch submission progress,
  which branches have change requests, or what remains before they can land.
---

# Upstreaming status

Produce a read-only snapshot of local source branches and their progress toward
the canonical upstream repository. Do not publish, rebase, prune, or otherwise
change branches while generating the report.

## Gather the evidence

1. Identify the canonical upstream remote and its default integration branch.
   Inspect remote URLs and remote `HEAD`; do not assume a remote named `origin`
   is canonical. If ownership or the canonical tracker is unclear, use the
   [`checking-upstream`](../checking-upstream/SKILL.md) skill.
2. Enumerate local branches and classify their role. Distinguish source branches
   intended for upstream from runtime, integration, release, and disposable
   mixdown branches. `wt list`, `git branch -vv`, branch configuration, and
   repository guidance each reveal different parts of the branch state.
3. Fetch only when current remote state is required and the active instructions
   permit network access. Otherwise state that counts or tracker status may be
   stale.
4. For every source branch, calculate divergence from the canonical upstream
   branch:

   ```bash
   git rev-list --left-right --count <upstream-ref>...<branch>
   ```

   The first number is upstream-only and the second is branch-only. Render them
   in `wt list` style as `↑<branch-only> ↓<upstream-only>`.
5. Query the canonical tracker for pull requests, merge requests, or equivalent
   submissions from each branch. Include open, draft, closed, and merged states;
   match the head repository owner as well as the branch name so similarly named
   branches from other forks are not confused.
6. Derive a short purpose summary from the change-request title, commit subjects,
   or diff. Append it after the branch name only when it adds meaning rather than
   restating words already present in the branch name.

Raw ahead/behind counts describe ancestry. A squash- or rebase-merged branch can
still appear ahead and behind; the canonical tracker's merged state wins when
classifying upstream progress. Use patch-equivalence checks such as
`git rev-list --cherry-pick` only when they help explain that discrepancy.

## Classify and order progress

Start every progress value with a meaningful status emoji. Use the closest
accurate wording rather than forcing every repository into a fixed lifecycle:

- `⚪` local only
- `🟡` fork published, no upstream submission
- `📝` draft submission
- `🔴` submitted but blocked, conflicting, or failing required checks
- `🟢` submitted and mergeable or otherwise ready for upstream review
- `⛔` closed or rejected without merging
- `✅` merged upstream

Order rows from least progress to furthest progress, with merged branches last.
Within the same stage, put blocked branches before ready branches. Never make an
emoji imply readiness that the tracker, CI, or review state does not support.

## Build and open the HTML report

Write report data to a temporary JSON file outside the repository. Use this
shape; `request` is optional and `stage` must be one of the status names above:

```json
{
  "repository": "owner/project",
  "canonical_url": "https://example.com/owner/project",
  "upstream_ref": "origin/main",
  "as_of": "2026-09-09 18:00 UTC",
  "summary": "Two branches need action; one is ready for review.",
  "stale": false,
  "branches": [
    {
      "name": "fix/example",
      "purpose": "keep choices visible while typing",
      "ahead": 5,
      "behind": 0,
      "stage": "published",
      "progress": "Fork published, no PR",
      "next_step": "Open PR"
    },
    {
      "name": "fix/other",
      "purpose": "expand lists into unused space",
      "ahead": 1,
      "behind": 5,
      "stage": "ready",
      "progress": "open, mergeable",
      "request": {
        "label": "PR #42",
        "url": "https://example.com/owner/project/pull/42"
      },
      "next_step": "Await review"
    }
  ],
  "runtime_notes": [
    "working is the published runtime mixdown, not an upstream submission branch."
  ]
}
```

Keep branch names, change-request numbers, counts, and tracker URLs exact. Keep
purpose and next-step text concrete and short. Set `stale` to `true` when remote
state was not refreshed.

Render the JSON with the bundled `scripts/render-report.py` into a temporary
`.html` file outside the repository. The renderer escapes dynamic content,
orders rows by progress, links change requests, and applies the bundled
responsive light/dark theme. Generated input and HTML files must not dirty the
repository.

Then load and follow [`open-in-user-browser`](../open-in-user-browser/SKILL.md),
the `/open` workflow, with the generated HTML file as its target. In chat,
report only that the browser report opened and give its path; do not repeat the
whole table unless browser opening fails or the user asks for the text.

Exclude mixdown and runtime-only branches from the progress rows by default.
Put them in `runtime_notes` when their role matters. If no source branches
qualify, use an empty `branches` array and explain that in `summary`.

## Related workflows

Use [`checking-upstream`](../checking-upstream/SKILL.md) when exact branch lookup
is insufficient, such as when looking for equivalent work, prior submissions,
or canonical tracker context.

Use [`submitting-upstream`](../submitting-upstream/SKILL.md) if the request moves
from reporting into preparing, updating, or publishing a submission, or when
contribution rules determine whether a branch is genuinely ready. A status
report alone never authorizes outward-facing changes.
