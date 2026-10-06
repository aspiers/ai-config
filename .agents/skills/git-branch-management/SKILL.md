---
name: git-branch-management
description: >-
  Structures git branches and worktrees: keeps unrelated changes on separate
  branches, isolates each in its own worktree created so the repository's
  setup runs, records dependencies with git-machete, and recombines them into
  a temporary mixdown branch for local testing. Use before creating any
  branch or worktree in a codebase that works on more than one branch,
  including branching off the default branch to start a change; when starting
  work in a fork, clone, or third-party checkout; when choosing what a new
  branch should be based on; when a branch is growing a second unrelated
  concern; when deciding whether to stack branches or keep them independent;
  when preparing a change for a pull request or patch submission; when handed
  an existing worktree or branch to implement and commit in a fork; or when a
  local build needs several in-progress branches combined. Not needed where
  the repository clearly commits everything to the trunk, or holds notes or
  personal data rather than code.
---

# Git Branch Management

Prepare every change in the form that is cleanest for upstream submission,
then recombine locally for testing and normal use.

## First establish upstream ownership

These principles exist to satisfy a maintainer you do not control. **Check who
owns the upstream before applying any of them.**

Inspect the remotes:

```bash
git remote -v
```

The usual convention names `origin` for the upstream and `github` for the
user's own fork of an upstream owned by someone else. Where it holds, a
`github` remote alongside `origin` suggests an upstream the user does not own.

A repository the user owns outright may have no `origin` at all — its only
remote can be `github`, pointing at their own account. So the absence of a
fork remote is not by itself a signal either way.

It is a convention rather than a rule, so read it as a hint about which URLs
to check, not as the answer. Ownership comes from the URLs themselves —
compare them against the user's own accounts and hosts. Ask if it stays
unclear.

Where the user owns the upstream there is no external reviewer to satisfy, so
clean separation stops paying for itself: combining concerns on one branch, or
pushing straight to the trunk, is legitimate and often preferable. Follow the
user's preference for that repository rather than imposing separation. Do not
spend effort splitting branches that nobody else will review.

## Why separation matters

Upstream reviewers accept or reject one concern at a time. When two
unrelated changes share a branch, the contentious one blocks the
uncontentious one: a maintainer who wants the bugfix must also litigate the
feature. Keeping them apart means each can land on its own schedule, and a
rejected change never strands an accepted one.

This is also why mixing beats arbitrary stacking. Stacking makes branch B
depend on branch A even when the two changes are unrelated, so B cannot be
submitted until A lands. Stack only where a real dependency exists; combine
independent branches with a mixdown instead.

## Isolate each branch in its own worktree

Develop each independent branch in its own worktree, so branches do not
contend for a single checkout and each keeps its own build state.

### Let the repository's own setup run

A new worktree is only usable once the repository's setup has run:
dependency install, env files, generated code. Each tool runs only its own
setup:

- `wt switch --create` runs hooks from `.config/wt.toml` and the user's
  worktrunk config, nothing else;
- Orca's `worktree create` runs the setup from the repository's `orca.yaml`
  (`scripts.setup`) or from Orca's settings for that repository;
- raw `git worktree add` runs neither, so never use it to start work.

Orca can only create a worktree when you are running inside it, which its
terminals signal by setting `ORCA_PANE_KEY`. So:

- inside Orca, in a repository with an `orca.yaml` or registered in Orca
  (`repo list --json`) with a setup script, create the worktree with Orca
  and start an agent in it, as the `orca-cli-local` skill describes; do
  not work in it from the current session unless the user says so;
- otherwise use `wt`, even when the repository has an `orca.yaml`:

```bash
wt switch --create <branch> --base <upstream-base>
```

`--base` matters here: without it `wt` uses the repository's default branch,
which is usually right, but an explicitly named base makes the intended
starting point unambiguous. See the `worktrunk` skill for configuration and
hooks.

If setup did not run, run it before editing: for a `wt` worktree in a
repository whose setup lives only in `orca.yaml`, run its `scripts.setup`
from the new worktree, with `ORCA_ROOT_PATH` set to the main checkout.
Never borrow another checkout's dependencies or build output. If the
repository has setup for only one tool, or none, propose adding a shared
script that both run: see the `setting-up-worktree-hooks` skill.

Reserve the main checkout for mixdowns and combined testing, matching the
default that `git-branch-mixer` describes.

`wt sync` rebases worktree branches onto their parents in dependency order,
which keeps a set of related branches current against a moving upstream
without rebasing each by hand:

```bash
wt sync --fetch          # fetch, then sync the current stack
wt sync --all --fetch    # sync every worktree branch
```

Prefer it over manual per-branch rebases when several branches need bringing
up to date. Combine with `--prune` to clear worktrees whose branches have
landed upstream. Note that `wt sync` and `git machete traverse` overlap; use
whichever the repository is already set up for rather than both at once.

## Choosing a base for new work

Base a new branch on the nearest upstream integration branch — typically
`origin/main` or `origin/master` — not on whatever branch happens to be
checked out. Deriving from a local feature branch silently makes that feature
a prerequisite of the new work.

Base on another local branch only when the new work genuinely cannot compile,
run, or make sense without it. Record that dependency in machete so the
relationship is explicit rather than implied by history.

A local checkout's base branch is not always named `main`; confirm what the
remote actually uses before branching.

### Integration fixes are real dependencies

When combining two branches needs more than a textual conflict resolution
(branch B moves code that branch A changes, so A's change must also be
applied in B's new location, or tests from both need reconciling), that is
a real dependency, not a mixdown concern. Stack the branch that needs
adapting on the other, record it in machete, and commit the fix on the
child branch. Do this without asking: it is this section's rule, not a
judgement call.

Never commit such a fix on `working` or hide it inside a merge commit.
Rerere replays only conflict hunks, so edits made inside a merge, and
commits made only on `working`, vanish at the next full rebuild. Before
rebuilding, check for both: commits on `working` that are on no source
branch, and differences between the old and rebuilt `working`.

The cost of separation is that no single branch contains everything, so a
build from one branch lacks the others' features. That is what mixdowns
resolve — they are the reason separation stays practical rather than merely
principled.

## Recording dependencies with git-machete

`git machete` maintains a branch layout file describing which branches descend
from which. It makes the intended tree explicit, shows sync state against
upstreams, and drives rebases that respect the structure.

```bash
git machete status          # tree plus sync state against parents and remotes
git machete discover        # infer an initial layout from existing history
git machete edit            # edit the layout file directly
git machete add <branch>    # place a branch in the tree
git machete traverse        # walk the tree, syncing each branch to its parent
```

Every worktree shares one layout file, by default in the main checkout's
git directory (`.git/machete`), unless
`machete.worktree.useTopLevelMacheteFile` is false. Get its path from
`git machete file` rather than building it yourself. If
`git machete status` prints a tree, a layout exists; with none it says "No
branches listed" and exits non-zero. Its yellow-edge warning means only
that a fork point was inferred, not the layout.

Roots sit unindented; each level of indentation marks a child of the branch
above. Independent features are siblings under the same root, never nested
inside one another:

```text
master
    feat/one
    feat/two
```

Reserve nesting for genuine prerequisites. A sibling layout is the signal
that two branches may be submitted in either order, and it is what makes them
eligible to be mixed rather than stacked. Annotations after a branch name can
record PR numbers and per-branch `traverse` qualifiers; see
`git machete help format`.

Run `discover` with care in a fork carrying many fetched upstream branches —
it proposes a layout from existing history, which may pull in branches you do
not maintain. Review its proposal before accepting.

## Recombining for testing and daily use

To build, run, or use the combined result, merge the independent branches
into a throw-away integration branch with a mixdown. The
`git-branch-mixer` skill owns the `ggmx` and `ggmxd` mechanics.

Source-branch scope and mixdown integration scope are independent. Keep each
source branch narrowly scoped for submission. The `working` mixdown must
include all configured source branches and always represent their latest
best-of-breed combination for day-to-day use and testing.

Never develop or commit new source work on `working`. Make and commit every
source change on its narrowly scoped source branch in that branch's worktree.

In a fork of an upstream the user does not own, with a `working` branch and
`mixdown.working` config (`git config --get-all mixdown.working`), add each
new source branch to the mix (`git mix +<branch>`) and to the machete layout
(`git machete add`) on its first commit, without asking. This is only
configuration: do it even when the main checkout is on another branch, so
the next mixdown includes the branch.

Regenerate `working` only where the user actually runs it, for example
checked out in the main checkout and served from there; mix config alone is
not enough. Even then, wait until a logically complete piece of work is
ready to test, such as when every commit a pull request needs has been
made, or a rebase or review fix finishes one. Intermediate commits are not
worth testing. Once it is ready, without asking:

- regenerate `working` from the full configured set in the main checkout
  (`git mixdown -c`);
- then rebuild and restart whatever serves the main checkout, so the user's
  own instance runs the new `working`. Look for it in user service units
  whose working directory is the main checkout, and in the project's README
  or agent instructions; ask if nothing turns up. A dev server you started in
  a feature worktree does not count.

Never update `working` from only the branch that changed. Stop and ask only
if the mixdown conflicts or would touch uncommitted changes in the main
checkout. If the main checkout is on another branch, ask before switching
it, and report the regeneration as pending. Never submit a branch upstream
until the user has had the chance to test it in their rebuilt instance.

`working` is a local scratch branch. Never push it or open a PR from it;
publish the independent source branches instead. This boundary keeps the
upstream-clean structure intact while still giving you a single working
build.

## When a branch accumulates unrelated work

Splitting after the fact is more expensive than starting separately, so
decide the shape when the work begins. If a branch has already grown a second
concern, move the newer concern onto its own branch off the upstream base,
record both in machete as siblings, and mix them for testing. The
[incremental-commits](../incremental-commits/SKILL.md) skill covers carving
existing changes into reviewable commits.

## Before submitting upstream

Confirm the branch contains only its own concern, sits on a current upstream
base, and carries no mixdown merge commits. See the
[submitting-upstream](../submitting-upstream/SKILL.md) skill for the
submission channel and its expectations.
