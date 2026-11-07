# Audit procedure

Read this file completely before the first audit step. The platform skill
supplies the commands for fetching the payload and the list of manifest
fields that execute code; this file says what to do with them.

## Execution freeze

Until the static audit passes and the user approves, do not:

- install, link, enable, approve, load or update the plugin through the
  platform, or run its commands, binaries, hooks or panels;
- run package installs (`npm`, `bun`, `pnpm`, `yarn`, `pip`), builds
  (`cargo build`, `make`, `go generate`), tests, linters or scripts from the
  candidate, or Nix flakes and devcontainers it ships;
- import or evaluate candidate code. Reading JSON or TOML as data is fine;
- let `direnv`, IDE tasks, Git hooks, language servers or previewers act on
  repository-controlled configuration;
- initialise submodules or fetch Git LFS content before inspecting and
  pinning their declarations.

Fetching registry metadata, tarballs, Git objects and public pages is
allowed, because none of it runs the candidate. Clone with hooks disabled and
without recursive submodules, into a new empty directory outside any managed
install path. Use `git diff --no-ext-diff --no-textconv` so
repository-configured diff helpers cannot run. Do not follow symlinks that
leave the checkout. Run scanners from a trusted install, not from the
candidate.

Do not copy settings, credentials, environment values, private registry URLs
or private notes into evidence or reports.

## 1. Pin identity and provenance

Record the source URL, the requested ref, the exact identity it resolved to
(commit SHA, version and integrity hash, or content hash), and every tag that
points at it. Confirm the ref resolves to that identity at install time too.

Look at provenance as evidence, not proof: repository and account age,
ownership changes or transfers, a changed maintainer, registry or integrity
hash, force pushes, archived or lookalike repositories, release pattern, and
signatures. A signed commit strengthens
provenance; it does not make code safe. An unsigned one is context, not a
rejection.

For an update, find the last approved identity and classify ancestry before
reading content:

```bash
git rev-list --left-right --count "$approved...$target"
git merge-base --is-ancestor "$approved" "$target"   # forward?
git merge-base --is-ancestor "$target" "$approved"   # downgrade?
```

A target that is an ancestor of the approved commit is a downgrade, whatever
the platform calls it. Diverged histories need an explicit fork review. Base
the verdict on the full content delta, not on commit messages.

## 2. Establish the complete scope

Inventory every tracked path, mode, symlink, submodule, LFS pointer and file
type. Default search tools skip hidden and ignored files, so list from Git
or the archive instead:

```bash
git ls-tree -r -t --full-tree "$target"
git ls-files --stage
git show "$target":.gitmodules 2>/dev/null
git ls-files -z | xargs -0 file --
```

Review the whole repository at the target, not only the plugin directory:
root workspaces, shared code and automation can affect a plugin in a
subdirectory. For a local tree, include untracked and ignored files that a
build or runtime command can reach.

Classify each path: manifest and entry points; runtime source; scripts and
wrappers; build, release, install, update and uninstall logic; dependency
manifests and lockfiles; build scripts, macros, generators and vendored code;
prompts, skills and instructions the plugin feeds to agents; tests, fixtures
and docs; CI and developer automation; binaries, archives, images and other
opaque content.

Keep a review ledger with one state per material path:

- `reviewed`: executable behaviour and any generated output inspected;
- `non-runtime`: docs or tests with no executable influence;
- `dependency pending`: dependency payload not yet established;
- `opaque`: binary, minified, or generated without matching source;
- `not reviewed`: still to do.

Any material `dependency pending`, `opaque` or `not reviewed` entry rules out
a safe verdict.

## 3. Map the execution surface

From the manifest, list everything the platform runs and when: entry
points, builds, startup, events, hooks, commands, panels, link handlers,
keybindings and settings that change behaviour. Note which run without the
user doing anything.

Trace each one to its end: every executable, imported module, dynamically
loaded file, environment expansion and subprocess. Watch for explicit
shells, built-up command strings, relative executables, `PATH` lookup, and
writable files that could replace an executable.

## 4. Establish effective authority

Write down two lists and compare them:

- **Declared:** the execution profile and capabilities the manifest asks
  for, as the platform's approval prompt will show them.
- **Effective:** what the execution model actually permits (a separate
  process as the user, a sandboxed frame, data only), plus every credential
  the code reads or could read from there. Look for the host application's
  control socket and token files, CLI binaries it can invoke, environment
  variables, agent sockets, SSH keys and cloud credentials.

When effective authority exceeds what the user will see at approval, report
the gap prominently, even when the current code uses it harmlessly. That gap
is what makes later versions risky.

## 5. Read every meaningful file

Pattern searches are triage. Every tracked text file gets a disposition in
the ledger, and every reachable entry point is traced, including dynamic
imports, reflection, generated code and error paths.

Investigate at least:

- process creation, shell interpolation, `eval`, `Function()`, dynamic
  imports, deserialisation, templates and FFI;
- outbound network, DNS, telemetry, analytics, webhooks, uploads, update
  checks, remote configuration and downloaded code or assets;
- reads or writes outside the plugin's own config and state, especially the
  home directory, `.ssh`, `.gnupg`, shell startup files, Git config, agent
  configs, browser profiles, cloud credentials and `/tmp`;
- environment harvesting, secret discovery, clipboard, terminal or pane
  scraping, key capture, process inspection and agent reads;
- writes back to the host application: terminal input, agent launches,
  settings, UI state, and any control API reached through a token;
- persistence through cron, systemd, launchd, shell profiles, autostart,
  global package installs or daemons;
- privilege changes: `sudo`, permission or ownership changes, devices,
  containers, SSH and remote execution;
- deletion, overwrite, recursive traversal, archive extraction, path
  traversal, races, unsafe temporary files and symlink following;
- obfuscation, encoded payloads, minified source, delayed or conditional
  behaviour, and checks on time, host or user;
- self-update and uninstall logic, and whether it verifies checksums or
  signatures;
- prompts, skills or docs that steer users or agents towards disclosing
  secrets or bypassing controls.

A first-pass search, to be explained hit by hit and supplemented with the
language's own APIs:

```bash
re='curl|wget|fetch\(|axios|requests\.|socket|net\.|http|webhook'
re+='|telemetry|analytics|eval\(|Function\(|exec\(|spawn|child_process'
re+='|subprocess|os\.system|sudo|ssh|chmod|chown|systemctl|launchctl'
re+='|crontab|\.ssh|\.gnupg|/etc/|/tmp/|HOME|TOKEN|SECRET|PASSWORD'
re+='|authToken|base64|import\('
git grep -nEI "($re)" "$target" -- .
```

Only after reading the code, read the changelog and release notes for the
range under review. Classify them as corroborated, incomplete, misleading,
absent or unverifiable.

## 6. Audit dependencies and the build chain

Inspect every dependency manifest and lockfile before materialising anything.
Look for:

- missing, stale or conflicting lockfiles, and broad version ranges without
  one (record what resolves today and that it can change);
- Git dependencies on branches or tags instead of full commits, and path
  dependencies that leave the repository;
- names resembling popular packages, and dependency confusion risk;
- lifecycle hooks (`preinstall`, `install`, `postinstall`, `prepare`),
  `setup.py` and build backends, Cargo `build.rs` and procedural macros, Go
  generators, Make targets, and downloaded release binaries;
- mutable or insecure download URLs, disabled integrity checks, overrides and
  vendored patches;
- native code and transitive packages with broad filesystem or network reach.

Compiling counts as execution when build scripts, macros or lifecycle hooks
run. For an update, compare the old and new dependency manifests first, and
review the payload of every material added or upgraded dependency.

Use trusted vulnerability scanners where they fit (`osv-scanner`,
`trivy fs`, `cargo audit`, `npm audit` on an existing lockfile, `pip-audit`,
`govulncheck`, `gitleaks`, Semgrep). Record versions and findings. Zero
findings is not approval.

If deeper checks need dependencies installed, do it only after the static
review passes, with locked or frozen modes and lifecycle scripts disabled,
in a disposable unprivileged environment with no secrets and no network
unless the build needs it.

## 7. Handle opaque or generated content

Do not approve an opaque executable, native library, archive, WASM module,
minified bundle without source, or generated artifact because a scanner
passed. Approval needs one of:

- the artifact is excluded from every build and runtime path;
- it was rebuilt from the audited source in a restricted environment and
  matches byte for byte;
- a trusted signed release and checksums were verified, reproducibility is
  documented as unavailable, and the user explicitly accepted the residual
  risk.

Otherwise the audit is `Inconclusive`. When both source and a bundled build
ship, review the bundle the platform loads; do not assume it came from the
source.

## 8. Repository automation

Audit `.github/workflows`, actions pinned by tag rather than commit,
`pull_request_target` jobs, secret-bearing jobs, release automation and bots.
This matters when forking or opening a pull request: a hostile workflow can
leak CI secrets even when the plugin's runtime is clean. Do not enable
workflows in a fork until they are understood.

## 9. Controlled execution

Only after the static review passes and the user approves:

1. Build or load in the most restricted environment practical.
2. Where feasible, capture process, filesystem and network behaviour
   (`strace`, process trees, a temporary `HOME` diff, firewall or proxy
   logs).
3. Run the narrowest action first, without real credentials or sensitive
   repositories.
4. Compare what happened with the manifest, the docs and the review.
5. Recheck the tree for generated or modified files.

Observation supplements review. Dormant or conditional paths may not run
during a test.

## Pacing a large audit

Work in passes: an inventory pass over every candidate (identities, changed
files, diff statistics, dependency and lifecycle changes); a review pass
taking small or decisive candidates first and security-sensitive files
before ordinary ones; then a completeness pass over the ledger. Keep each
candidate's evidence separate. Save oversized output to files and read it in
bounded sections or per-file diffs rather than one huge diff.

Stop deep review early only when a concrete severe finding already justifies
`Do not install` or `Do not upgrade`, or when missing or opaque evidence
makes a complete review impossible after the highest-risk paths are checked.
A sampled large diff is `Inconclusive`.
