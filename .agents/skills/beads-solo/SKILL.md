---
name: beads-solo
description: >-
  Configure and enforce Beads policy for an opt-in project maintained
  initially by one owner. Use when a repository has a root .beads-solo marker
  or when the user explicitly asks to enroll a repository in the
  solo-maintainer workflow.
  Layers server-mode Dolt, maintainer identity, Git ignores, JSONL recovery
  export, and AGENTS.md discovery rules on top of the beads skill.
---

# Beads Solo

This is a policy layer. Use the [`beads`](../beads/SKILL.md) skill for the
normal Beads workflow and CLI guidance; do not duplicate it here.

## Scope Gate

Before any Beads mutation, resolve the Git root and check the opt-in marker:

```bash
root=$(git rev-parse --show-toplevel)
test -f "$root/.beads-solo"
test ! -L "$root/.beads-solo" && test ! -s "$root/.beads-solo"
git -C "$root" ls-files --error-unmatch -- .beads-solo >/dev/null
```

The tracked root `.beads-solo` must be a regular, empty file.

- If it is absent, stop without changing the repository. Create it only when
  the user explicitly asks to enroll this repository.
- If it is non-empty or not a regular file, stop and report the malformed
  marker.
- Do not infer participation merely from the presence of `.beads/`.

A participating repository must also have a tracked top-level `AGENTS.md`
containing `beads-solo` and telling agents to use this skill. Verify the exact
instruction with:

```bash
git -C "$root" ls-files --error-unmatch -- AGENTS.md >/dev/null
grep -Fq 'Use the `beads-solo` skill' "$root/AGENTS.md"
```

During enrollment, add a minimal statement such as:

```markdown
## Beads Solo

Use the `beads-solo` skill for Beads setup and maintainer policy in this
repository. Use the `beads` skill for the standard Beads workflow.
```

During normal work, stop and report a policy error if `AGENTS.md` is absent or
does not mention `beads-solo`. Do not silently choose a different instruction
file.

## Additional Policy

Apply only these rules beyond the `beads` skill:

1. Use Dolt **server mode**, never embedded mode.
2. Record this clone's role as the maintainer in repository-local Git config.
3. Keep generated Dolt data and runtime files out of Git using Beads' current
   canonical ignore rules.
4. Keep the regular issue graph recoverable in Git through automatic JSONL
   export.
5. Do not grant commit, push, or sync authority. Current user, repository, and
   upstream `beads` policy still control those operations.

“Solo” describes current ownership, not an incompatible storage format. Keep
normal Beads IDs, dependencies, and history so collaborators can be added
later.

## Enroll or Repair a Repository

### 1. Establish the governance files

Only after explicit enrollment approval:

```bash
: > .beads-solo
```

Ensure the top-level `AGENTS.md` contains the statement above and add both
governance files to Git before running `bd` setup. If no top-level `AGENTS.md`
exists, stop and report that it must be created or supplied; do not invent
repository-wide instructions implicitly.

### 2. Initialize in server mode

Ensure `bd`, the standalone `dolt` CLI, and the intended `dolt sql-server` are
available. For a new workspace, use:

```bash
bd init --server --role maintainer --agents-profile minimal
```

Use the environment's configured host, port, socket, user, and password when
they differ from Beads defaults. Never fall back to plain `bd init`.

For an existing workspace, inspect `.beads/metadata.json`. Require
`"dolt_mode": "server"`. If it says `embedded`, stop: do not edit metadata or
move database directories by hand. Migration requires an explicitly approved,
full `bd backup` and restore flow from the upstream Dolt documentation.

### 3. Pin the maintainer role

Set and verify the repository-local Git variable:

```bash
git config --local beads.role maintainer
test "$(git config --local --get beads.role)" = maintainer
```

`beads.role` is the Beads source of truth for maintainer/contributor routing.
Do not rely on remote-URL heuristics.

### 4. Configure Git-tracked JSONL recovery state

Use Beads' built-in auto-export and auto-staging:

```bash
bd config set export.path issues.jsonl
bd config set export.auto true
bd config set export.git-add true
bd config set import.path issues.jsonl
bd config set import.auto true
bd hooks install
```

The resulting `.beads/issues.jsonl` contains regular issues plus their labels,
dependencies, and comments. Beads intentionally excludes memories,
infrastructure beads, templates, and ephemeral records from automatic export;
do not add a custom hook that publishes them. Track `.beads/config.yaml` and
`.beads/metadata.json` for the remaining portable operating configuration.

Upstream calls this an **export**, not a full backup. It is a Git-durable,
issue-level recovery path if Dolt state is lost, but it does not preserve Dolt
branches, commit history, working sets, or every database table. Use
Dolt-native `bd backup` or a Dolt remote when full recovery is required.

### 5. Install and verify canonical ignores

Do not copy a frozen ignore list into this skill. Let the installed Beads
version own it:

```bash
bd doctor --dry-run
# After checking that the proposed repairs are appropriate:
bd doctor --fix --yes
bd doctor
```

If the dry run proposes data repair, deletion, or migration beyond canonical
ignore and integration maintenance, obtain explicit approval before applying
it.

The policy outcome is:

- track `.beads/.gitignore`, `.beads/config.yaml`, `.beads/metadata.json`, and
  `.beads/issues.jsonl` when it exists;
- ignore `.beads/dolt/`, `.beads/embeddeddolt/`, `.beads/proxieddb/`, native
  backup data, credentials, environment files, locks, sockets, logs, PIDs,
  export state, and legacy databases;
- keep root safeguards such as `.dolt/`, `*.db`, `.beads-credential-key`, and
  `.beads/proxieddb/` ignored;
- never ignore the whole `.beads/` directory; and
- never add negation rules to `.beads/.gitignore`, because they can defeat
  contributor/fork exclusions.

Use `git check-ignore` and
`git status --short -- .beads .gitignore` to confirm that runtime data is
ignored while the portable files remain visible.

## Recovery and Ongoing Checks

After setup and after Beads upgrades, run:

```bash
bd doctor
bd config get export.auto
bd config get export.git-add
bd config get export.path
git config --local --get beads.role
```

Also verify that `.beads/metadata.json` still selects server mode and that the
root marker and `AGENTS.md` declaration remain present.

If Dolt data is missing but the tracked JSONL survives, stop normal work and
use the upstream recovery/bootstrap guidance. Inspect the JSONL and obtain
approval before any restore that could overwrite a non-empty database.
