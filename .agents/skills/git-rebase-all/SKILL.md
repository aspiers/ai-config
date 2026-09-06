---
name: git-rebase-all
description: >-
  Rebases every local branch of a fork onto a moved upstream, flags the ones
  upstream has superseded, and rebuilds the mixdown branch that combines them.
  Use after fetching a fork's upstream and finding it has advanced far, been
  force-pushed, or rewritten its history; when several stacked or sibling
  branches all need bringing forward at once; when a branch was cut from a
  mixdown and now carries merge commits it should not have; or when asked to
  rebase all branches, re-mix, or bring a whole worktree set up to date.
---

# Rebasing a whole branch set onto a moved upstream

[`git-branch-management`](../git-branch-management/SKILL.md) owns the branch
*shape* — one concern per branch, siblings over stacks, mixdowns for local
testing. This skill covers moving that shape forward when the upstream it
rests on has moved, which is where the expensive mistakes happen.

The order matters: **survey, then decide, then rebase parents before
children, then re-mix.** A rebase started before the survey is finished tends
to be a rebase done twice.

## 1. Survey before touching anything

Establish four things first. Each one changes what the right answer is, and
none is visible from `git log` on a single branch.

**Did upstream rewrite history, or just advance?** After a force-push the old
base is gone, so every branch looks thousands of commits "ahead" when it is
really just parented on a commit that no longer exists. Compare *trees*, not
commit counts — identical trees under different SHAs is the signature of a
rewrite, and it means nothing of yours was lost:

```bash
git rev-parse <old-base>^{tree} <suspected-upstream-equivalent>^{tree}
```

Find the equivalent by searching upstream for a distinctive commit subject
from the old base. `git log --oneline --all --grep=<subject>` showing the same
message at two SHAs confirms the rewrite.

**Which branches are already superseded?** Look for the feature upstream, not
for your commits — a maintainer who implemented the same idea differently has
superseded your branch just as surely as one who merged it. Check whether the
files, symbols, or user-visible strings exist upstream now.

**Which branches correspond to open PRs?** `gh pr list --author @me --state
all` — and note that "has a PR" and "has commits worth keeping" are
independent. A closed-unmerged PR whose feature landed another way is
obsolete; an unpushed branch may still be the most valuable thing in the set.

**Do any branches carry mixdown merge commits?** A branch cut from `working`
rather than from upstream contains an octopus merge and re-contains its
siblings' commits. It is not submittable and must be re-parented, not merely
rebased. `git log --merges <branch> ^<upstream>` finds them.

Record the findings before starting. The survey is also what tells you two
branches are the same commit — a duplicate is common after a mixdown and is
cheaper to notice now than to rebase twice.

## 2. Put the structural choices to the user

Rebasing a large set is not reversible in practice, so the decisions that
shape it belong to the user, asked together and up front via
**AskUserQuestion** rather than discovered mid-rebase:

- how to re-parent a mixdown-tainted branch (onto its real prerequisite, or
  flattened onto upstream);
- what to push, given that "branches with open PRs" may turn out to be none;
- how far to go on conflicts — resolve fully, or stop and report.

## 3. Back up, then rebase parents before children

Create a backup ref per branch before the first rebase. It costs nothing and
converts every later mistake into a `git branch -f`:

```bash
ts=$(date +%Y%m%d-%H%M%S)
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
  git branch "backup/$ts/$b" "$b"
done
```

Enable `rerere` first (`git config rerere.enabled true`). Sibling branches in
a stack hit the *same* conflict repeatedly, and a recorded resolution turns
the second and third encounters into no-ops.

Rebase in dependency order, root first, each child onto its already-rebased
parent:

```bash
git rebase --onto <rebased-parent> <old-parent-tip> <branch>
```

`--onto` with an explicit old-parent tip is what keeps a child from dragging
its parent's pre-rebase copies along. For a branch cut from a mixdown, the
old-parent tip is the merge commit itself — naming it drops both the merge
and the siblings' commits in one move.

`wt sync --all --fetch` can do this for a set already described to worktrunk
or machete; prefer it when the layout is recorded and conflicts are expected
to be light, and fall back to explicit per-branch `--onto` when
re-parenting.

## 4. Resolving conflicts against a rewritten codebase

Most conflicts in this situation are not semantic disagreements — they are
your change landing next to a refactor. The recurring shapes:

- **Additive collisions** (a registry, an import list, a fixture array): both
  sides add. Take both. These are the majority.
- **A renamed parameter or type** (`session` → `scope`, `PaneRead` →
  `MuxGrid`): apply upstream's new name to your added code. The typechecker
  finds every straggler, so resolve the conflict first and let `tsc` list the
  rest.
- **A helper that moved scope**: upstream hoisted or extracted what you
  edited. Delete your copy, and re-apply your change at the new home.
- **A block that moved entirely**: upstream extracted your edit site into a
  shared function and left the old inline copy dead, or deleted it. Take
  upstream's side wholesale, then re-apply your one-line change at the *live*
  call site. Verify which site is live — resolving into dead code produces a
  clean rebase and a silently missing feature.
- **A new required field on an interface you construct**: look at how sibling
  implementations fill it before inventing a value; the honest default is
  usually already established next door.

**Generated or golden files are regenerated, not hand-merged.** Find the
producing script or test, run it, then diff the result against the previous
version and confirm the delta is only what you expect.

When resolving changes what a golden records, check whether the change is a
*correction*. A test rewritten to consult a registry may legitimately
classify fixtures differently than the hand-maintained chain it replaced —
that is the fix working, provided the payload each row carries is unchanged.

Fold fixes discovered while testing into the commit that owns them
(`git commit --fixup=<sha>` then `git rebase --autosquash`), so the branch
stays a series of coherent changes rather than accumulating repair commits.

## 5. Version files in a fork are the maintainer's

A release commit or version bump on a fork branch conflicts with upstream's
own releases every single time. If the project reserves versioning to the
maintainer (many do — check its contributor guidance), **drop those commits
and hunks** rather than resolving them: `git rebase --skip` for a whole
release commit, and restore the upstream content for version files caught in
a mixed commit. Confirm afterwards that the project's own version check still
passes and that the branch shows no diff against upstream for those paths.

## 6. Establish the pre-existing failure baseline

Before attributing any test failure to the rebase, run the same test on clean
upstream. A suite inherited from a moved upstream often arrives already red,
and a failure that reproduces on untouched upstream is not yours to fix —
report it, do not chase it. The same applies to suites that hang or time out
only when run together.

## 7. Re-mix and verify

Update `git machete` to the new layout and clear stale fork-point overrides
(`git machete fork-point --unset-override <branch>`), which a rewrite
invalidates and which otherwise produce noisy false warnings.

Then rebuild the mixdown from the *leaf* branches — including a parent
separately only when nothing descends from it — and verify the combination,
not just the individual branches. The `git-branch-mixer` skill owns the `ggmx`
and `ggmxd` mechanics.

Finish by confirming, explicitly:

- every branch sits on the new upstream, with no merge commits
  (`git log --merges <branch> ^<upstream>` empty for each);
- version files are untouched relative to upstream, where that rule applies;
- the mixdown typechecks, tests, and builds;
- any remaining failure also fails on clean upstream.

## Reporting

Say plainly which branches were rebased, which were **flagged obsolete** and
on what evidence (feature present upstream, PR closed unmerged, no unique
commits), which were deleted as duplicates, and which are ready to push. A
branch declared obsolete should name the upstream thing that superseded it,
so the user can check the judgement rather than take it on trust.

Leave the backup refs in place and say where they are.
