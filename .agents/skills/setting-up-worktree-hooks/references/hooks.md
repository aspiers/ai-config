# Wiring the script into worktrunk and Orca

Read this when writing or debugging `.config/wt.toml` or `orca.yaml`. Each
hook stays one plain command line, with all logic in the script.

## worktrunk (`.config/wt.toml`)

```toml
# Worktrunk project hooks: https://worktrunk.dev/hook/

# A new worktree has no dependencies or local env files, so nothing else
# works until this runs. pre-start blocks post-start hooks and `--execute`
# until it finishes.
[pre-start]
setup = "sh scripts/worktree-setup.sh"
```

- Use `pre-start` for setup that later steps depend on. worktrunk otherwise
  prefers `post-start`, which runs in the background.
- The hook runs with the new worktree as its working directory.
- Steps in a `[pre-start]` table run in order. A failing step stops the
  rest.
- Project hooks need the user's approval. **Tell the user to run
  `wt config approvals add`. Never pass `--yes` for them**: approving a
  repository's hooks is their security decision.
- Approval covers the command line, not the script's contents. Editing the
  script needs no new approval, so review script changes as you would the
  hook itself.
- `wt hook pre-start` re-runs the hook, even in a worktree wt did not
  create. Without a TTY it cannot prompt for approval, so it fails until
  the user has approved the hooks.

See the `worktrunk` skill for the config format and template variables.

## Orca (`orca.yaml`)

```yaml
# Orca worktree config:
# https://github.com/stablyai/orca/blob/main/docs/site/content/docs/model/orca-yaml.mdx

scripts:
  setup: sh scripts/worktree-setup.sh

# An agent started before setup finishes would find no dependencies.
setupAgentStartupPolicy: wait-for-setup
```

- **`scripts.setup` comes from the new worktree's `orca.yaml`**, so it only
  works for worktrees whose base branch already has the file.
- **`worktree.sharedDirectories` and `.worktreeinclude` are read from the
  primary checkout's copy.** Changing them on a branch has no effect until
  the primary checkout has them. Treat both as Orca-only optimisations: the
  script must not depend on them.
- On macOS and Linux, setup runs under a Bash runner with `set -e`.
  `ORCA_ROOT_PATH` (primary checkout) and `ORCA_WORKTREE_PATH` are set.
- **On native Windows, the runner is a `.cmd` file** that calls each line.
  A command line with no `$VAR` references, such as
  `node scripts/worktree-setup.mts`, runs unchanged there. `sh …` needs Git
  Bash.
- **A parse error disables setup, tabs and shared directories together.**
  Duplicate keys count as parse errors.
- **Settings → Repository → "Command source & orca.yaml" can silently
  override the file.** "Local only" runs the user's local hook and ignores
  `orca.yaml`. It is the default whenever the user has a non-empty local
  setup hook. Only the user can change it, and no CLI exists for it, so
  report it to them.
- The Setup terminal stays open as a shell after setup finishes. Waiting
  for it to exit never returns: read its output instead (see
  `orca-cli-local`).
- To see what Orca actually ran, read the runner it writes under the
  worktree's git directory. One version used
  `.git/worktrees/<name>/orca/setup-runner.sh`.

## Plain `git worktree add`

This runs neither hook. Run `sh scripts/worktree-setup.sh` by hand from the
new worktree.

Some package managers refuse to run scripts before the first install, so a
package-manager alias for the script (Yarn 4's `yarn <script>`, for
example) suits only re-runs. Check this per package manager in a
fresh worktree.
