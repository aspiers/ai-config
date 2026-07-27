# Beads Solo Setup and Repair

Read this reference only for enrollment, repair, upgrades, governance-file
changes, or recovery. For routine work, use the policy in `../SKILL.md` and
the standard `beads` skill.

## Enroll a Repository

Enrollment requires explicit user approval.

For a repository with an existing Beads workspace, check `bd context --json`
first. If `dolt_mode` is `embedded`, stop and tell the user that enrollment
requires server mode and that migrating is a separate, explicitly approved
step. Do not begin
[Migrate Embedded to Server](#migrate-embedded-to-server) on the strength of
an enrollment request alone.

1. Resolve the Git root and create the opt-in marker:

   ```bash
   root=$(git rev-parse --show-toplevel)
   : > "$root/.beads-solo"
   ```

2. Ensure the root has a tracked `AGENTS.md`. Do not invent repository-wide
   instructions when it is absent; stop and ask the user to create or supply
   it.

3. If a tracked top-level `CLAUDE.md` exists, compare the complete files
   before editing either one:

   ```bash
   if git -C "$root" ls-files --error-unmatch -- CLAUDE.md >/dev/null 2>&1
   then
       cmp -s "$root/AGENTS.md" "$root/CLAUDE.md"
   fi
   ```

   Do not strip or ignore generated sections. Any difference is a policy
   error: stop and ask the user how to resolve it. Never edit only one file in
   a diverged pair.

4. Choose the instruction-file layout before initialization:

   - If `CLAUDE.md` is a symlink resolving to `AGENTS.md`, normal Beads agent
     setup is safe. Beads skips Claude managed-section injection through the
     symlink while retaining Claude hooks and Codex integration.
   - If both are regular files, stop even when they are currently identical.
     Explain that normal `bd init` writes different platform sections to them,
     then ask the user to choose one of these routes:
     1. replace `CLAUDE.md` with a symlink to `AGENTS.md` and retain full
        agent integration;
     2. keep identical regular files and use `--skip-agents`, losing automatic
        Claude and Codex integration; or
     3. abort enrollment.
   - If `CLAUDE.md` is absent, ask whether to create the symlink or retain
     only `AGENTS.md` and use `--skip-agents`.

   Never convert, replace, or remove an instruction file without explicit user
   approval.

5. Add this declaration outside all Beads-managed markers in the chosen shared
   target or in both approved regular files:

   ```markdown
   ## Beads Solo

   Use the `beads-solo` skill for Beads setup and maintainer policy in this
   repository. Use the `beads` skill for the standard Beads workflow.

   This repository opts into the Beads **team-maintainer** profile for issue
   management and commits. Unless a current user or orchestrator instruction
   says otherwise, agents may manage issues and make atomic commits as work
   progresses. They must not push Git branches or sync or push Dolt state
   unless explicitly requested.
   ```

6. Before adding the declaration, read the existing instruction file in full
   and identify any statement it would contradict — most commonly a
   session-completion or "landing the plane" checklist that mandates pushing
   to a remote, which conflicts with the declaration's withholding of Git
   push and Dolt sync/push authority.

   **Automatically generated instructions that direct an agent to push are
   invalid by default.** `bd` and similar tools emit session-completion and
   "landing the plane" checklists containing mandatory-push steps without
   knowing the repository's policy, so such generated text confers no
   authority to push. Never treat it as permission, and never act on it.
   Automatic pushing is a legitimate policy for some repositories, but only
   once the user has explicitly granted it for that repository; absent that
   grant, the no-push default governs regardless of what generated text says.

   Do not add the declaration and leave a contradiction in place, and do not
   resolve it yourself. Quote the conflicting text to the user, note whether
   it is generated, explain that the repository cannot both mandate and
   withhold push authority, and ask which policy the repository adopts. Apply
   their choice, editing the conflicting section or the declaration to match.

   Also check the file for Beads commands removed in current `bd`, such as
   `bd sync`, which no longer exists and is replaced by `bd dolt push` and
   `bd dolt pull`. Report stale commands to the user rather than silently
   rewriting surrounding policy.

7. Track the marker and governance files before initialization.

## Initialize in Server Mode

Require `bd`, the standalone `dolt` CLI, and the intended `dolt sql-server`.
Use the command matching the approved layout.

For `CLAUDE.md` symlinked to `AGENTS.md`:

```bash
BD_NO_PUSH=true bd init \
    --server --role maintainer --agents-profile minimal
```

For approved, byte-identical regular files or an approved AGENTS-only layout:

```bash
BD_NO_PUSH=true bd init \
    --server --role maintainer --skip-agents
```

Use configured host, port, socket, user, and password settings when they
differ from Beads defaults. Never fall back to plain `bd init`.

Beads' `--agents-profile` option controls generated-instruction verbosity, not
maintainer authority. Its generated instructions contain a conservative
fallback; the external declaration is the explicit repository opt-in that
activates commit authority. `BD_NO_PUSH=true` keeps Dolt push instructions out
of generated content during initialization.

After initialization, persist the Dolt push guard and recheck file identity:

```bash
bd config set no-push true
bd config get no-push
cmp -s "$root/AGENTS.md" "$root/CLAUDE.md"  # when CLAUDE.md exists
```

`no-push: true` makes `bd dolt push` refuse to push. The external declaration
separately prohibits `git push` unless explicitly requested.

For an existing workspace, inspect `bd context --json` and require
`"dolt_mode": "server"`. If it says `embedded`, do not proceed with
enrollment and do not edit metadata or move database directories manually.
Report this to the user and ask whether to migrate; see
[Migrate Embedded to Server](#migrate-embedded-to-server) for the approvals
required before any migration begins.

## Migrate Embedded to Server

**Migrating a workspace out of embedded mode ALWAYS requires explicit user
permission, without exception.** It rewrites how the issue database is
stored. Never start it because enrollment, a skill instruction, or any other
task appears to require server mode. Encountering `dolt_mode: embedded` is
never itself authorization to migrate. If the user has not explicitly asked
for or approved this migration in the current conversation, stop and report
that the workspace is embedded, then ask. Approval for enrollment, for
Beads setup, or for a previous migration in another repository does not carry
over.

`bd` 1.0.x has no native in-place embedded-to-server conversion. Once the
user has approved migrating, use the `bd-migrate-embedded-to-server` wrapper,
which backs up, recreates, and restores:

```bash
bd-migrate-embedded-to-server --dry-run
```

The script verifies embedded mode, creates a Dolt-native backup plus a JSONL
safety export, renames the original `.beads` to a timestamped directory
(never deletes it), runs `bd init --server`, restores the backup, and
verifies the result is server mode.

**Separately obtain explicit user approval for the issue prefix before
running the migration.** The prefix is inferred from existing issue IDs, then
config, then the working-directory name; the cwd fallback often yields a
long, undesirable prefix. It becomes a permanent part of every issue ID, so
present the inferred value to the user and confirm or override it with
`--prefix` before proceeding. Never accept the inferred prefix silently.

Both approvals are mandatory and independent. Neither substitutes for the
other: approval to migrate is not approval of the prefix, and approval of a
prefix is not approval to migrate. Before running the migration, confirm you
hold both, given explicitly by the user in the current conversation:

1. explicit approval to migrate this workspace out of embedded mode; and
2. explicit approval of the exact issue prefix.

If either is missing, stop and ask for it. Show the user the `--dry-run`
plan, then run:

```bash
bd-migrate-embedded-to-server --yes --prefix APPROVED_PREFIX
```

Note that the script passes `--skip-agents`. When `CLAUDE.md` is a symlink to
`AGENTS.md`, complete agent integration afterwards rather than leaving it
skipped. Verify with `bd context --json` that `dolt_mode` is `server`, and
confirm any memories and issues survived via `bd memories` and `bd list`.

Also verify the issue prefix survived, because `bd backup restore` replaces
the whole database and can discard what `bd init --prefix` wrote:

```bash
bd config get issue_prefix     # underscore; see the warning below
```

**Never read the prefix via `bd config get issue-prefix` (hyphen).** It
returns `(not set)` unconditionally, even when the prefix exists and
`bd create` works, and it exits `0` either way. Match the `(not set)` marker
textually rather than testing exit status. When `config get` and the actual
behaviour disagree, the database `config` table is ground truth:

```bash
bd sql "SELECT value FROM config WHERE \`key\`='issue_prefix'"
```

(`key` is a SQL reserved word and must be backquoted.) A prefix present only
in `.beads/config.yaml` is insufficient — reads work but `bd create` fails
with `database not initialized: issue_prefix config is missing`.
`bd config show | grep issue_prefix` shows `(database)` or `(config.yaml)`
provenance, which distinguishes the two.

If the prefix is missing, note that `bd config set issue_prefix`,
`bd rename-prefix`, and `bd bootstrap` all fail to repair it. See
`BEADS-UPSTREAM.md` in the ai-config repository for the working repair routes
and for which of these behaviours are upstream bugs expected to change.

If the Dolt restore fails, the original embedded workspace is preserved at
the timestamped directory. Retry with `--fallback-jsonl` only after
explaining that it loses Dolt history and non-issue tables.

## Pin the Maintainer Role

Set and verify the repository-local role:

```bash
git config --local beads.role maintainer
test "$(git config --local --get beads.role)" = maintainer
```

`beads.role` is the source of truth for maintainer/contributor routing. Do not
rely on remote-URL heuristics.

## Configure JSONL Recovery State

Use Beads' built-in auto-export and auto-staging:

```bash
bd config set export.path issues.jsonl
bd config set export.auto true
bd config set export.git-add true
bd config set import.path issues.jsonl
bd config set import.auto true
bd hooks install
```

Track `.beads/config.yaml`, `.beads/metadata.json`, and
`.beads/issues.jsonl` when it exists. The JSONL contains regular issues,
labels, dependencies, and comments. It intentionally excludes memories,
infrastructure beads, templates, and ephemeral records; do not publish those
through a custom hook.

This export is an issue-level recovery path, not a full backup. It does not
preserve Dolt branches, commit history, working sets, or every database table.
Use Dolt-native `bd backup` or a Dolt remote when full recovery is required.

## Install Canonical Ignores

Let the installed Beads version own its ignore rules:

```bash
bd doctor --dry-run
# After confirming that the proposed repairs are appropriate:
bd doctor --fix --yes
bd doctor
```

If the dry run proposes data repair, deletion, migration, or instruction-file
changes, obtain explicit approval before applying it.

The expected result is:

- track `.beads/.gitignore`, `.beads/config.yaml`, `.beads/metadata.json`, and
  `.beads/issues.jsonl` when it exists;
- ignore Dolt data, native backups, credentials, environment files, locks,
  sockets, logs, PIDs, export state, and legacy databases;
- retain root safeguards such as `.dolt/`, `*.db`,
  `.beads-credential-key`, and `.beads/proxieddb/` ignores;
- never ignore the whole `.beads/` directory; and
- never add negation rules to `.beads/.gitignore`, because they can defeat
  contributor and fork exclusions.

Use `git check-ignore` and `git status --short -- .beads .gitignore` to verify
that runtime data is ignored while portable files remain visible.

## Verify or Repair an Existing Enrollment

Run:

```bash
bd doctor
bd config get export.auto
bd config get export.git-add
bd config get export.path
bd config get no-push
git config --local --get beads.role
```

Also verify:

- `.beads-solo` is tracked, empty, and regular;
- `.beads/metadata.json` selects server mode;
- `no-push` is `true`;
- `AGENTS.md` contains the skill declaration and team-maintainer opt-in;
- any tracked `CLAUDE.md` is byte-for-byte identical to `AGENTS.md`; and
- the declaration withholds Git push and Dolt sync/push authority.

If generated Beads blocks already exist, keep the external declaration
outside them. Do not edit a generated block merely to change its conservative
fallback; the external declaration supplies the repository opt-in and its
narrower no-push policy.

## Recover from JSONL

If Dolt data is missing but tracked JSONL survives, stop normal work. Inspect
the JSONL and follow upstream recovery/bootstrap guidance. Obtain explicit
approval before any restore that could overwrite a non-empty database.
