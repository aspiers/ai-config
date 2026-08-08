---
name: upstreaming-changes
description: >-
  Contribute a local change back to an upstream open-source project by first
  discovering and obeying that project's own contribution guidelines, then
  preparing a compliant branch, commits, and change-request description. Use
  when upstreaming a patch, fix, or feature, submitting a pull request or
  merge request to someone else's project, or sending a patch to a project's
  mailing list.
---

# Upstreaming Changes

Submit a change to a project you don't control, in the form that project
actually asks for.

The failure this skill exists to prevent is an embarrassing submission: a PR
that ignores the project's stated conventions — wrong branch, unsigned
commits, missing changelog entry, wrong commit message style, no tests, or
opened on a forge the project doesn't use. Discovering the rules is the main
work; the git mechanics are the easy part.

Accordingly: **a change that violates upstream's guidelines does not get
submitted.** Report the violation and fix it, or explain why it can't be
fixed. See "Refuse to Submit Non-compliant Work" below for the narrow
override.

## When to Use This Skill

- Upstreaming a local fix, workaround, or feature to its origin project
- Opening a pull request or merge request against a repository you don't own
- Sending a patch to a project that takes contributions by mail
- Checking whether a change you already prepared complies with upstream rules

## Non-negotiable Order

**Read the guidelines before writing or rewriting a single commit.** The rules
determine the branch you fork from, how commits must be split and worded,
whether a sign-off or CLA is required, and what must accompany the change.
Reworking commits afterwards wastes effort and risks shipping a
non-compliant submission.

## Process

### 1. Establish what is being upstreamed, and to where

Identify the local change (branch, commits, working-tree diff, or a patch
applied to a vendored copy) and the **canonical** upstream — not a fork,
distro package, or read-only mirror. If either is ambiguous, ask.

Signals for the canonical home: the URL in package metadata, `README`, the
repository's own description, and where recent releases and issue activity
actually happen. A GitHub repo marked "forked from" or archived is not it.

### 2. Check for existing work

Use the `checking-upstream` skill to search the tracker and open change queue
for the same problem. An existing merged fix, open change request, or explicit
"wontfix" decision changes the whole plan — possibly to "don't submit".

### 3. Gather the contribution guidelines

Collect every source that exists; don't stop at the first one. Absence of a
file is itself information, not permission to invent conventions.

Look for:

- `CONTRIBUTING.md` / `CONTRIBUTING.rst` / `CONTRIBUTING` (repo root, `docs/`,
  `.github/`, `.gitlab/`)
- `.github/PULL_REQUEST_TEMPLATE.md` (or `.md` files under
  `PULL_REQUEST_TEMPLATE/`), `.gitlab/merge_request_templates/`
- `CODE_OF_CONDUCT.md`, `DCO`, `CLA.md`, `LICENSE` (relicensing or
  copyright-assignment expectations)
- `docs/` developer, hacking, or contributor guides; a project website's
  contributing page; a wiki
- Machine-enforced rules, which are guidelines with teeth: CI workflow files
  (`.github/workflows/`, `.gitlab-ci.yml`), `.pre-commit-config.yaml`,
  `.editorconfig`, linter and formatter configs, `commitlint` config,
  `.git-blame-ignore-revs`
- `AGENTS.md`, `CLAUDE.md`, or similar, if upstream ships one
- The project's own recent history: `git log` on the default branch, and two
  or three recently **merged** change requests, which reveal the conventions
  actually enforced by maintainers versus the ones merely documented

For a repository you have locally, read these from the checkout. Otherwise
fetch them from the forge. Prefer the project's own documentation over
inference; where documented and observed practice disagree, note the conflict
rather than silently picking one.

### 4. Extract a concrete checklist

Turn what you found into an explicit, verifiable list. Typical items:

- **Target branch** — default branch, or a `develop`/`next`/release branch?
  Are stable-branch backports handled separately?
- **Submission channel** — pull request, merge request, mailing-list patch
  series, patch tracker, or a forge other than where the mirror lives.
- **Legal** — DCO sign-off (`git commit -s`), CLA signature, copyright header
  or `AUTHORS` update, licence of new files.
- **Commit conventions** — message format (Conventional Commits, imperative
  subject, subject length, wrapping), granularity, whether fixups must be
  squashed, whether merge commits are refused in favour of rebase, issue
  reference syntax (`Fixes #123`).
- **Code conventions** — formatter, linter, language version, style guide.
- **Accompanying changes** — tests, documentation, changelog or news fragment
  (`CHANGELOG.md`, `towncrier` newsfragments, `debian/changelog`), type stubs,
  translations, generated files.
- **Process expectations** — file an issue first for non-trivial changes,
  discuss on a mailing list or chat before implementing, one logical change
  per submission, draft-PR etiquette, size limits.
- **Local verification** — the exact test, lint, and build commands upstream
  expects to pass, and which CI jobs will run.

Report this checklist to the user before doing the work. If a rule would
materially change the shape of the change (for example: "open an issue and get
agreement first", or "this project does not accept feature contributions"),
raise it now rather than after the branch is built.

### 5. Prepare the contribution

Only once the checklist exists:

1. **Sync with upstream.** Add the canonical repository as a remote if needed
   and fetch it. Never assume `origin` points upstream — in a fork it might
   or might not.
2. **Branch from the required target branch as discovered above**, freshly
   fetched. A branch based on a stale or wrong base produces a noisy diff.
3. **Port the change onto that branch** — cherry-pick, rebase, or reapply.
   Strip anything local and irrelevant: personal config, personal or sensitive
   data, irrelevant debug output, unrelated formatting churn, vendored-copy
   artefacts.
4. **Shape the commits to the documented conventions.** One logical change per
   commit unless upstream says otherwise. Rewrite messages to match observed
   style. Apply sign-off if required. Consider the `incremental-commits` skill
   when the change spans several concerns.
5. **Add the accompanying changes** the checklist demands — tests, docs,
   changelog entry.
6. **Run upstream's own verification commands** and report results honestly. A
   submission that fails the project's test suite is exactly the embarrassment
   this skill prevents.

### 6. Draft the submission text

Follow the project's PR/MR template literally if one exists — keep its
headings and fill every section, rather than substituting your own structure.
The `describing-prs` skill can generate the body; adapt its output to the
template rather than the reverse.

Include what upstream asks for: motivation, what changed, how it was tested,
linked issue, and any documented boilerplate. Match the project's tone.

### 7. Report and stop

**Do not push to a fork, open the change request, or send the patch without
explicit approval.** Submitting is outward-facing and hard to retract.

Present:

- the compliance checklist, each item marked satisfied, not applicable, or
  unmet (with the reason);
- what the branch contains and what base it sits on;
- verification command output;
- the drafted submission text;
- the exact commands that would submit it, ready to run.

Then wait.

#### Refuse to Submit Non-compliant Work

**If any checklist item is unmet, the default answer is no.** Do not prepare
the submission commands as though the change were ready, and do not soften an
unmet item into a caveat buried in a summary. Say plainly which guideline is
violated, quote or cite where upstream states it, and either fix it or explain
why it can't be fixed.

This holds even when the user asks to go ahead: a request to "just submit it"
is not permission to ignore a rule the user may not know about. Surface the
violation first and let them decide with the facts.

Push back hardest on the items maintainers notice immediately — wrong target
branch, missing sign-off or CLA, commit messages that don't match the required
format, failing tests or lint, a missing changelog entry, unrelated changes
mixed in, or submitting through a channel the project doesn't use.

**Overriding requires an explicit, informed instruction** — the user
acknowledging the specific violation and directing you to proceed anyway
("yes, submit without the changelog entry"). A generic "go ahead", "looks
good", or "ship it" is not an override. When overridden:

- proceed with the rest of the work in full;
- state the violation in the change request itself, where the maintainer will
  see it, rather than hoping it goes unnoticed;
- don't relitigate it afterwards.

Some guidelines are not overridable by the user at all, because compliance
isn't theirs to waive: a CLA or DCO sign-off asserts something on another
party's behalf, so never add `Signed-off-by:` for a person who hasn't agreed
to it, and never assert a CLA has been signed when it hasn't.

### 8. After submission

Once the user has submitted, use the `pr-comment-resolving` skill to handle
review feedback, and the `watching-ci-runs` skill to follow upstream CI.

## Forge and Channel Notes

The process above is forge-agnostic; the mechanics differ.

**GitHub** (most common). `gh` CLI throughout: `gh repo view` for metadata,
`gh repo fork --remote` to fork, `gh pr list --search` for existing work,
`gh pr create --base <branch> --body-file <file> --draft` to submit. Read
templates from `.github/` in the checkout, or via `gh api` when working
remotely. Pipe long `gh` output through `tee` into `tmp/` for repeated
analysis.

**GitLab.** Merge requests via `glab mr create`; templates under
`.gitlab/merge_request_templates/`; CI rules in `.gitlab-ci.yml`. Many
GitLab projects require the source branch to live in a personal fork.

**Gitea / Codeberg / Forgejo.** GitHub-like PR model; `tea` CLI where
available, otherwise the web UI. Templates in `.gitea/` or `.github/`.

**Mailing list / patch series.** Common in kernel- and toolchain-adjacent
projects. Expect `git format-patch` + `git send-email`, a cover letter for
multi-patch series, `Signed-off-by:` on every commit, strict subject prefixes
(`[PATCH v2 1/3] subsystem: summary`), and versioned resends with a changelog
below the `---`. Check `MAINTAINERS`, `get_maintainer.pl`, or the project's
submission guide for the correct recipients and list — and check whether
patches are still accepted there at all, since some projects have migrated.

**Other trackers** (Gerrit, Phabricator, Bugzilla-with-patches, Launchpad).
Read the project's submission documentation before assuming a workflow;
Gerrit in particular needs a `Change-Id` hook and pushes to
`refs/for/<branch>`.

## Notes

- The project's rules win over any personal or repository-level convention,
  including this repo's own commit style. You are a guest.
- Never invent a guideline. If something is unspecified, follow the pattern in
  recently merged work and say that's what you did.
- If the change is large, unsolicited, or architectural, check whether
  upstream wants an issue or discussion first. Many projects reject such PRs
  on process grounds alone.
- Rebase-and-force-push to the submission branch is normal during review, but
  only after checking upstream's stated preference — some projects want
  additional commits so reviewers can see what changed.
