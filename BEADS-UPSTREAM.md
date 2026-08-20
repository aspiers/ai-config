# Beads upstream quirks and watch list

Behaviour of upstream [Beads](https://github.com/steveyegge/beads) that local
tooling depends on, and that is expected to change. Re-check this file when
upgrading `bd`, because several workarounds here become wrong once the
corresponding upstream bug is fixed.

Verified against **bd 1.0.5 (dev: master@4d08edbeb772)** on 2026-07-27.

## Reading the issue prefix

`bd config get issue-prefix` (hyphen) returns `(not set)` unconditionally,
**even when the prefix exists and `bd create` works**. Only the underscore
form is reliable:

```bash
bd config get issue_prefix     # correct
bd config get issue-prefix     # ALWAYS reports "(not set)" — never use
```

Exit status is `0` in both the set and unset cases, so callers must match the
`(not set)` marker textually rather than test `$?`.

Ground truth is the database `config` table, which is what bd's own
"database not initialized: issue_prefix config is missing" check consults:

```bash
bd sql "SELECT value FROM config WHERE \`key\`='issue_prefix'"
```

`key` is a SQL reserved word; without backquotes the query fails with
`syntax error at position 11 near 'key'`.

`bd config show | grep issue_prefix` reports provenance — `(database)` or
`(config.yaml)` — which matters because a prefix present only in
`.beads/config.yaml` is not sufficient: reads succeed but `bd create` fails.

**Watch:** upstream
[#3494](https://github.com/steveyegge/beads/issues/3494) (open) asks for
`config get`, `config show` and the strict check to agree. If it is fixed, the
hyphen form may start working and the underscore form may change; verify both
before trusting either.

## Repairing a missing issue prefix

When the database has no `issue_prefix` row, `bd create` fails and all three
documented repair paths are dead ends:

| Command | Result |
|---|---|
| `bd config set issue_prefix X` | refused outright |
| `bd rename-prefix X` | `Error: failed to get current prefix: <nil>` |
| `bd bootstrap` | reports success, does not persist it |

Two routes actually work:

```bash
# Sanctioned, but re-initializes local data
bd init --server --reinit-local --prefix X --database DB --non-interactive

# Raw SQL escape hatch (upstream #4827); use INSERT when the row is absent
bd sql "UPDATE config SET value='X' WHERE \`key\`='issue_prefix'"
bd sql "CALL DOLT_COMMIT('-A','-m','fix issue_prefix cell')"
```

**Watch:**
[#3494](https://github.com/steveyegge/beads/issues/3494) and
[#4827](https://github.com/steveyegge/beads/issues/4827) (both open) request a
first-class non-destructive setter or a `--repair` mode. If one lands, prefer
it over both routes above, and drop the `restore_prefix` reinit from
`bin/bd-migrate-embedded-to-server`.

`bd rename-prefix` requires a trailing hyphen (`dc-`), unlike
`bd init --prefix` (`dc`). It also doubles the prefix
(`atlas-atlas-*`) when stored IDs already carry the target prefix — see
[#4827](https://github.com/steveyegge/beads/issues/4827).

## Prefix loss during embedded-to-server migration

`bd backup restore` replaces the entire database, discarding the
`issue_prefix` that `bd init --prefix` wrote moments earlier. A source
workspace that never had a prefix therefore produces a migrated workspace
without one, and the migration otherwise reports success.

`bin/bd-migrate-embedded-to-server` compensates via `restore_prefix()`, which
runs after the restore, plus a final check that fails loudly rather than
leaving a workspace where `bd create` does not work.

**Watch:** [#3723](https://github.com/steveyegge/beads/issues/3723)
(*"`bd init` doesn't seed `issue_prefix` config row when a town transitions
from embedded to server-mode dolt"*) is closed as completed, but its body is
**redacted**, so it is unknown what was fixed or whether the fix is present in
1.0.5. The symptom still reproduces on 1.0.5. Re-test after any upgrade; if it
stops reproducing, `restore_prefix()` becomes a no-op and can be retired.

## Uncommitted config rows

`DoltStore.Commit()` deliberately excludes the `config` table (citing GH#2455,
"skip config to avoid sweeping up stale issue_prefix changes"), so writes made
by `bd init` are never committed and sit in the working set indefinitely.

Visible as `bd doctor` reporting `Dolt Status: config modified` on an
otherwise healthy workspace. `bd vc status` reports clean, because it only
considers staged changes.

Root cause documented in
[#3216](https://github.com/steveyegge/beads/issues/3216) (closed/completed),
same class as #3028 / PR #3052.

## Config keys that bypass config.yaml

`bd config set import.auto true` reports success **without** the
`(in config.yaml)` suffix that the other keys print, and the value is stored
in the database rather than the file. It therefore does not travel with a
fresh clone the way file-based keys do. `export.path`, `export.auto`,
`export.git-add` and `import.path` all land in `config.yaml` as expected.

## config.yaml formatting

`bd config set` writes `config.yaml` **without a trailing newline**, violating
`insert_final_newline = true` in `.editorconfig`. Re-add it after any
`bd config set` in a repository that enforces editorconfig.

## GitHub issue search is unavailable

`gh issue list --repo steveyegge/beads --search ...` silently returns nothing,
and the search API returns HTTP 422 (*"the listed users and repositories
cannot be searched"*) despite the repository being public and listable. Every
`--search` result is a false negative.

Fetch and filter locally instead:

```bash
gh issue list --repo steveyegge/beads --state all --limit 800 \
    --json number,title,state,updatedAt > issues.json
```

Note the 800-issue ceiling; the repository has more, so absence from a local
filter does not prove absence upstream.

## Workspace walk adopts ~/.beads when it contains embeddeddolt/

Observed on **bd 1.2.1** (2026-08-20). When no repo-local `.beads/` exists,
`FindBeadsDir` can escape the repo/worktree boundary — despite its own
resolution-order comment saying the walk stops there — and adopt the global
`~/.beads` directory as the project workspace. The trigger is
`hasBeadsProjectFiles` counting an `embeddeddolt/` subdirectory as project
files (`internal/beads/beads.go:696`), which defeats the guard whose comment
says it exists precisely to prevent returning `~/.beads`. An old-era global
embedded database at `~/.beads/embeddeddolt/` therefore makes every
unenrolled directory under `$HOME` resolve to `~/.beads`.

Reproduced from a git worktree (t3 layout, `.git` file) whose main repository
had no `.beads/`: `bd context` reported `beads_dir: /home/adam/.beads` with
`cwd_repo_root` correctly set to the worktree — so repo detection worked, but
the walk boundary was not enforced. From the main checkout (regular `.git`
directory) the same probe correctly reported no workspace, so the escape may
be worktree-specific.

Consequences observed in sequence:

1. `bd init --server` half-initializes: the Dolt server, database,
   `config.yaml`, and `metadata.json` all land in `~/.beads`, and **no
   repo-local `.beads/` anchor is created** — `bd init`'s own closing
   diagnostics report `Installation: No .beads/ directory found` while still
   printing `bd initialized successfully!`.
2. With old-era `embeddeddolt/` alongside the freshly written server-mode
   files, every subsequent command fails with `legacy Dolt server workspace
   detected; explicit migration is required`, wedging `bd` for any directory
   that resolves to `~/.beads`.

Workaround: move the old `~/.beads/embeddeddolt/` (and any stray
server-mode files a half-init wrote: `config.yaml`, `metadata.json`, `dolt/`,
`hooks/`, `dolt-server.*`) out of `~/.beads`, leaving only registry files
(`registry.json`, `machine-id`, `backup/`). After that, resolution correctly
reports no workspace, and `bd init` from a worktree targets the main
repository root via the worktree fallback as intended.

**Watch:** if upstream tightens `hasBeadsProjectFiles` to exempt `~/.beads`
(or enforces the documented walk boundary), the quarantine workaround becomes
unnecessary; re-test workspace resolution from a worktree after any upgrade.
