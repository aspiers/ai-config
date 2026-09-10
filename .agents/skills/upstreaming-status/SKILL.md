---
name: upstreaming-status
description: >-
  Reports how local Git branches are progressing toward canonical upstream
  inclusion as a compact terminal table plus a browser-rendered HTML report,
  with branch purpose, stack dependencies, Git Machete topology, ahead/behind
  counts, change-request status, and next action. Use when asked for upstreaming
  status, local branch submission progress,
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
3. Capture `git machete status` and use its configured parent-child topology to
   identify stacked branches. For each source branch, record every qualifying
   source branch that must land first, ordered from the stack root to the direct
   parent. Do not treat the integration branch as a dependency or infer logical
   dependencies from commit ancestry when Machete explicitly says otherwise.
4. Fetch only when current remote state is required and the active instructions
   permit network access. Otherwise state that counts or tracker status may be
   stale.
5. For every source branch, calculate divergence from the canonical upstream
   branch:

   ```bash
   git rev-list --left-right --count <upstream-ref>...<branch>
   ```

   The first number is upstream-only and the second is branch-only. Render them
   in `wt list` style as `↑<branch-only> ↓<upstream-only>`.
6. Query the canonical tracker for pull requests, merge requests, or equivalent
   submissions from each branch. Include open, draft, closed, and merged states;
   match the head repository owner as well as the branch name so similarly named
   branches from other forks are not confused.
7. Derive two descriptions from the change-request title and body, commit
   subjects, or diff:
   - a short purpose phrase for the terminal table, adding meaning rather than
     merely restating the branch name;
   - a sentence-length description for the HTML report that explains what the
     change does and why it matters.

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

## Report in the terminal

Always return the compact table in chat, even when the HTML report opens:

| Branch and purpose | `<upstream-ref>` ↕ | Upstream progress | Next step |
|---|---:|---|---|
| `fix/inline-freeform-answer` · keep choices visible while typing | ↑5 ↓0 | 🟡 Fork published, no PR | Open PR |
| `fix/number-custom-response` · activate custom input using number keys | ↑1 ↓5 | 🔴 PR #41 open, conflicting | Rebase |
| `fix/overlay-list-height` · show more choices when prompt space is unused | ↑1 ↓5 | 🟢 PR #42 open, mergeable | Await review |
| `fix/overlay-toggle-kitty-events` · prevent release events toggling twice | ↑1 ↓5 | ✅ PR #40 merged | Prune branch |

Keep this terminal version terse, with exact branch names, change-request
numbers, counts, and a concrete next step. Format every branch name as monospace
code in both report versions, including dependency lists. Link change-request
numbers when URLs are available.

## Build and open the additional HTML report

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
  "machete_graph": "main\n|\no-fix/example\n  |\n  o-fix/other",
  "branches": [
    {
      "name": "fix/example",
      "purpose": "keep choices visible while typing",
      "description": "Keeps canned choices visible during custom-answer entry.",
      "dependencies": [],
      "ahead": 5,
      "behind": 0,
      "stage": "published",
      "progress": "Fork published, no PR",
      "next_step": "Open PR"
    },
    {
      "name": "fix/other",
      "purpose": "expand lists into unused space",
      "description": "Uses spare overlay height to reduce scrolling.",
      "dependencies": ["fix/example"],
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
`purpose` and `next_step` concrete and short for the terminal table. Make each
`description` a useful sentence for the roomier HTML report, not a padded copy
of the purpose phrase. Set `dependencies` to the ordered source-branch chain for
stacked branches and to `[]` for stack roots. Store the ANSI-stripped Machete
status output in `machete_graph`; if Machete is unavailable, put the exact reason
there rather than inventing a graph. Set `stale` to `true` when remote state was
not refreshed.

Render the JSON with the bundled `scripts/render-report.py` into a temporary
`.html` file outside the repository. The renderer escapes dynamic content,
orders rows by progress, shows stack dependencies per branch, links change
requests, and renders the Git Machete graph in a separate preformatted section.
Generated input and HTML files must not dirty the repository.

Then load and follow [`open-in-user-browser`](../open-in-user-browser/SKILL.md),
the `/open` workflow, with the generated HTML file as its target. In chat,
return the compact terminal table and state that the richer browser report
opened, including its path. If browser opening fails, report that failure and
still return the terminal table.

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
