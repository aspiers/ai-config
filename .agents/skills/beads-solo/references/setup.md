# Beads Solo Setup and Repair

Read this reference only for enrollment, repair, upgrades, governance-file
changes, or recovery. For routine work, use the policy in `../SKILL.md` and
the standard `beads` skill.

## Enroll a Repository

Enrollment requires explicit user approval.

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

6. Track the marker and governance files before initialization.

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

For an existing workspace, inspect `.beads/metadata.json` and require
`"dolt_mode": "server"`. If it says `embedded`, stop. Do not edit metadata or
move database directories manually. Migration requires an explicitly approved
full `bd backup` and restore flow following upstream Dolt documentation.

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
