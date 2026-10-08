---
name: setting-up-worktree-hooks
description: >-
  Gives a repository one idempotent, repo-local worktree setup script (local
  env files, dependency install, build steps) that worktrunk's
  `.config/wt.toml` pre-start hook and Orca's `orca.yaml` scripts.setup both
  call, so every new git worktree is usable at once. Use when adding or fixing
  worktree setup hooks, writing `wt.toml` or `orca.yaml` setup, when new
  worktrees lack dependencies or `.env` files, or when asked to make worktrees
  "just work" in a repo. For creating a worktree in a repo that already has
  setup, use `git-branch-management` instead.
---

# Setting up worktree hooks

A fresh worktree lacks everything git doesn't track: dependencies,
gitignored env files, generated code and caches. Each worktree tool runs
only its own hook, and raw `git worktree add` runs none. So give the repo
**one script that owns setup**, and have every tool call it:

```text
.config/wt.toml   [pre-start] ──┐
orca.yaml   scripts.setup ──────┼──> scripts/worktree-setup.<ext>
by hand after git worktree add ─┘
```

`git-branch-management` covers *using* this setup when creating worktrees.
This skill covers *adding* it to a repo.

## 1. Survey before writing

- **What a new worktree lacks.** List the gitignored files in the primary
  checkout, e.g. `git ls-files --others --ignored --exclude-standard
  --directory`. Note which of them the app or tooling actually reads, plus
  the install, codegen and build steps a working checkout needs.
- **Existing hooks and scripts.** Extend what is there rather than adding a
  parallel path.
- **Repo conventions.** Use its script directory, language, test framework,
  license headers and comment style.
- **Check every precedent's stated reason before copying it.** An existing
  script's "plain JS because tsx isn't installed yet" may no longer hold:
  Node ≥ 22.18 strips TypeScript types natively. Re-check claims about
  tooling versions, missing features or platform limits against the repo's
  current toolchain. Likewise, a precedent that spawns `npx.cmd` without a
  shell is itself broken on Node ≥ 18.20.2 and ≥ 20.12.2 (see below).

## 2. Write the script

**Pick the language.** POSIX `sh` suits a script that mostly runs other
commands, and needs nothing installed. Use the repo's main language when its
interpreter is guaranteed present before install, and when the logic
deserves unit tests in the repo's own framework. Worked examples, to adapt
rather than copy:

- [references/worktree-setup.sh](references/worktree-setup.sh) (POSIX sh)
- [references/worktree-setup.mts](references/worktree-setup.mts) (Node,
  native TypeScript, with injectable install for tests)

**The contract:**

- **Idempotent.** Every re-run is harmless: skip what exists, and let the
  install itself be a no-op.
- **Runs before install**, so it uses built-ins or the standard library
  only, never the project's own dependencies.
- **Finds the primary checkout itself, and never guesses.** Take the first
  entry of `git worktree list --porcelain -z`, and trust it only if `git -C
  <entry> rev-parse --show-toplevel` succeeds and equals it, comparing real
  paths. Otherwise there is no primary checkout: skip linking. Don't derive
  it from `--git-common-dir`: for a worktree of the bare repo
  `/srv/project.git` that gives `/srv`, and an unrelated `/srv/.env.local`
  gets linked in. Checking for `bare` alone is not enough either: after
  `git init --separate-git-dir`, the first entry is the metadata directory.
  Capture or discard git's stderr, so the expected failure prints nothing.
  This works the same under wt, Orca and plain git, and keeps the hook
  lines free of `$VAR`/`%VAR%` differences.
- **Skips file linking when it runs in the primary checkout**, comparing
  real paths.
- **Spawns package managers through a shell on Windows only**, e.g.
  `spawnSync("npm", ["install"], { shell: process.platform === "win32" })`.
  Node can't resolve `npm`/`yarn`/`npx` shims without a shell, and since
  CVE-2024-27980 it [refuses to spawn `.cmd` or `.bat` files without
  one][cve] (EINVAL), so naming `npm.cmd` is no fix. Keep the arguments
  constant or properly quoted, since the shell parses them.
- **Fails hard on steps a working tree needs** (install, codegen, build).
  Steps that only fail on a flaky network or a private resource just warn,
  as long as a later step would catch a genuinely broken install. Pass the
  install's exit code through.
- **Comments say why** each step exists and why it is ordered as it is.

## 3. Local env and other gitignored files

- **Symlink by default.** Link each needed gitignored file from the primary
  checkout, so one source of truth serves every worktree and a rotated
  secret reaches them all. **Copy only files a branch writes to
  independently**, such as per-branch databases or caches that tasks
  modify.
- **Never replace an existing path, dangling links included.** In `sh`,
  test `[ -e "$f" ] || [ -L "$f" ]`: a dangling link fails `-e`, and `ln`
  would then abort a re-run under `set -e`. In Node, `symlinkSync` refuses
  any existing path and raises `EEXIST`. Skip files missing from the
  primary.
- **Never print file contents**, and don't spread secret files nothing
  reads.
- Where the repo tracks `*.example` files that map one-to-one onto the real
  ones, derive the list from them (`git ls-files '*.env*.example'`), so new
  packages are covered. Otherwise keep an explicit list.
- **Never share dependency trees** such as `node_modules` or virtualenvs
  between checkouts. They can hold relative or absolute links back into
  their own checkout.
- **Audit `.gitignore` while there.** Make sure every local secret file is
  ignored. Check with `git check-ignore -v --no-index <path>`, and confirm
  that no tracked file became ignored with `git ls-files -ci
  --exclude-standard`.

## 4. Wire up the hooks

Call the interpreter directly, e.g. `sh scripts/worktree-setup.sh` or `node
scripts/worktree-setup.mts`, not a package-manager script: some package
managers refuse to run scripts before the first install. A package-manager
alias is still handy for manual re-runs.

Read [references/hooks.md](references/hooks.md) for the `wt.toml` and
`orca.yaml` snippets and their gotchas. **Two of these are the user's to
do, never the agent's:**

- approving worktrunk hooks (`wt config approvals add`);
- setting Orca's Settings → Repository → "Command source & orca.yaml" to
  **orca.yaml only** or **Run both**, if a local hook would otherwise
  override the file.

Link to the official docs in config comments, and **open every link before
committing it**.

If the repo's CI lints YAML or TOML, make sure it covers the new files:
extend the existing workflow rather than adding another.

## 5. Verify

1. Run the unit tests where the script has them, against real `git init`
   plus `git worktree add` repos in temp directories, with the install
   stubbed. Cover:
   - links a file when it is missing;
   - never replaces an existing file, or a dangling link;
   - skips a file missing from the primary;
   - skips linking in the primary checkout;
   - finds the primary from a subdirectory;
   - finds no primary for a worktree of a bare repo, or of a
     `--separate-git-dir` checkout, and never links a `.env.local` planted
     beside `project.git`;
   - re-runs are harmless;
   - passes the install's exit code through;
   - spawns the install with a shell on `win32` only (mock
     `node:child_process`, and make the platform a parameter).
2. Create a throwaway worktree from a branch that has the new files, with
   each tool the repo uses (`wt switch --create`, Orca with setup set to
   run). Confirm dependencies, links and builds are in place.
3. Run the script again by hand, and once via any package-manager alias:
   both must be no-ops.
4. Remove the throwaways. Check that removing one didn't follow a link and
   delete anything in the primary checkout.

## 6. Document it

Add a short "Worktrees" note to the repo's `AGENTS.md` (or its equivalent).
Say what the script sets up, which hooks call it, and the manual command
after a plain `git worktree add`.

[cve]: https://nodejs.org/en/blog/vulnerability/april-2024-security-releases-2
