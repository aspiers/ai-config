# Audit procedure for Pi packages

Load the `auditing-third-party-plugins` skill and read its procedure and
verdict references completely before using this file, unless the parent
skill's explicitly invoked maintainer-authored fork exception applies. That
skill owns the principles, the execution freeze, the review ledger, the
generic review checklist, verdicts and report contents. This file adds what
is specific to Pi: which packages to audit, how to obtain the payload Pi
would load, and what Pi itself executes.

## Scope

- If package names or sources were supplied, audit only those.
- A supplied package that is not installed is a fresh-install candidate. Audit
  its complete executable payload and dependencies rather than inventing an
  installed-to-target delta, and use install-specific wording in the report.
- Otherwise, audit every installed Pi package with an available upgrade. Do
  not discover or recommend unrelated fresh installs by default.
- Include user and trusted project packages. Deduplicate the same package
  identity, noting which scope wins.
- Treat npm specs containing a version and Git sources containing `@ref` as
  pinned. Pi does not advance them automatically; report this if explicitly
  requested, but do not invent an upgrade target.
- Local-path packages have no remote upgrade target. Report that when named.

## Pi commands frozen during an audit

On top of the shared execution freeze, do not run `pi update`, `pi install`
or `npx`, load candidate resources into Pi, or check out candidate Git code
into the installed worktree.

Create one unique temporary evidence directory and save a machine-readable
status file plus package-specific artifacts there. Use stable sanitized
package names. Run independent registry or fetch operations with bounded
concurrency (four workers is a reasonable default), but review each candidate
serially so findings are not mixed.

## 1. Discover candidates

Run `pi list` to obtain configured sources and managed install paths. Use the
installed `package.json` and Git checkout as local ground truth; a package or
extension manager's update badge is only a hint.

For each unpinned npm source:

1. Read `<managed-path>/package.json` to get the package name and installed
   version.
2. Query the configured registry without installing:

   ```bash
   npm view <package-name> version dist.integrity --json
   ```

3. It is a candidate only when the registry version differs from the
   installed version.

For each unpinned Git source:

1. Record the installed commit, configured `origin`, current branch, and
   tracked upstream. Do not assume the upstream belongs to `origin`.
2. Mirror Pi's target selection. Use the tracked branch only when it is an
   `origin/<branch>` ref; otherwise query `origin`'s remote `HEAD` and flag
   the mismatch. This matters for checkouts whose local branch tracks a fork:

   ```bash
   installed=$(git -C <repo> rev-parse HEAD)
   upstream=$(git -C <repo> rev-parse --abbrev-ref \
     '@{upstream}' 2>/dev/null || true)
   if [[ $upstream == origin/* ]]; then
     ref="refs/heads/${upstream#origin/}"
   else
     ref=HEAD
   fi
   git -C <repo> fetch --quiet --no-tags origin "$ref"
   target=$(git -C <repo> rev-parse FETCH_HEAD)
   ```

3. Classify ancestry as the shared procedure describes, with the installed
   commit as the approved identity. A target Pi labels an update can still be
   a downgrade.
4. It is a candidate only when the commits differ. Record the exact origin
   URL, selected ref, target commit, and ancestry classification in the
   evidence, but avoid exposing private URLs in the final report.

If discovery fails for one package, continue and report its evidence gap.

## 2. Inspect the payload Pi would load

Audit the payload Pi would load, not merely the repository's release page.

### npm packages

For a fresh install, query the exact version's metadata and fetch its published
`dist.tarball` URL into the evidence directory with `curl`. Verify the archive
against `dist.integrity`, list and extract it without running scripts, then
review every material shipped file and dependency. The absence of an installed
version is not a reason to use `npm diff` against an invented baseline.

For an upgrade, compare the two published tarballs directly:

```bash
npm diff \
  --diff=<package-name>@<installed-version> \
  --diff=<package-name>@<target-version> \
  --diff-name-only

npm diff \
  --diff=<package-name>@<installed-version> \
  --diff=<package-name>@<target-version> \
  -- package.json <changed-runtime-paths...>
```

Start with the file list and metadata. Do not request one enormous full diff
when selective path diffs will do. Group changed paths into package metadata,
runtime, generated/bundled, binaries, prompts/skills, docs, and tests; then
ask `npm diff` only for the next review group.

The published tarball is authoritative even when compiled output differs from
upstream source. If `npm diff` cannot retrieve both payloads, do not
substitute changelog claims for missing code.

### Git packages

For a fresh install, resolve the requested/default ref to an exact commit and
fetch a source archive or objects into the evidence directory without running
repository code. Inspect the complete package root, Pi resources, root and
workspace manifests, dependencies, lifecycle scripts, submodules, and
downloaded or generated artifacts.

For an upgrade, fetch objects without changing the installed checkout:

```bash
git -C <repo> fetch --quiet --no-tags origin refs/heads/<branch>
target=$(git -C <repo> rev-parse FETCH_HEAD)
git -C <repo> diff --no-ext-diff --no-textconv \
  --name-status HEAD "$target"
git -C <repo> diff --no-ext-diff --no-textconv \
  HEAD "$target" -- package.json <changed-runtime-paths...>
```

Start with `--name-status`, `--numstat`, package manifests, lockfiles, and
lifecycle scripts, then per-directory or per-file runtime diffs.

For monorepos, first determine which root and workspace manifests Pi
discovers, which resources are active, and which lifecycle script runs at the
managed checkout root. Do not audit every workspace equally when only a
subset can be loaded, but do include root install behavior and shared
dependencies.

## 3. Pi-specific checks

Follow the execution path from `package.json` and its `pi` manifest or
conventional resource directories. Extensions run with full user privileges;
skills, prompts and themes still change agent behaviour, so review them as
instructions. In addition to the shared checklist, look for:

- expanded tool behaviour, permissions, prompt or system instructions, hooks,
  or automatic actions;
- peer-dependency and required Pi API or version changes;
- configuration migrations, changed defaults, renamed commands or tools, and
  state-format changes.

Distinguish behaviour introduced by the candidate from lifecycle behaviour
that Pi re-runs during any Git checkout update: an unchanged `prepare` script
can still mutate the checkout or download artifacts.

## Pi verdict policy

Use the shared verdicts. Presume that keeping Pi packages current is
desirable after a complete audit, so `Upgrade with caution` must carry one of
the shared actions rather than act as a reason to defer by default.
