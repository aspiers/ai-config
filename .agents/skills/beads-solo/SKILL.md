---
name: beads-solo
description: >-
  Enforce Beads policy for an opt-in repository maintained initially by one
  owner. Use when a repository has a root .beads-solo marker or when the user
  asks to enroll, repair, or operate a solo-maintainer Beads workspace. Grants
  issue-management and commit authority while requiring explicit permission
  for Git pushes and Dolt sync or push operations.
---

# Beads Solo

This is a policy layer. Use the [`beads`](../beads/SKILL.md) skill for normal
Beads workflow and CLI guidance; do not duplicate it here.

## Apply on Every Use

1. Resolve the Git root and validate the opt-in marker:

   ```bash
   root=$(git rev-parse --show-toplevel)
   test -f "$root/.beads-solo"
   test ! -L "$root/.beads-solo" && test ! -s "$root/.beads-solo"
   git -C "$root" ls-files --error-unmatch -- .beads-solo >/dev/null
   ```

   The marker must be a tracked, empty, regular file. If it is absent or
   malformed, stop. Create it only when the user explicitly requests
   enrollment; never infer participation from `.beads/` alone.

2. Validate the repository policy declaration:

   ```bash
   git -C "$root" ls-files --error-unmatch -- AGENTS.md >/dev/null
   grep -Fq 'Use the `beads-solo` skill' "$root/AGENTS.md"
   grep -Fq 'opts into the Beads **team-maintainer** profile' \
       "$root/AGENTS.md"
   ```

   If any check fails, stop and report a policy error.

3. If a top-level `CLAUDE.md` is tracked, require its complete contents to be
   byte-for-byte identical to `AGENTS.md`:

   ```bash
   if git -C "$root" ls-files --error-unmatch -- CLAUDE.md >/dev/null 2>&1
   then
       cmp -s "$root/AGENTS.md" "$root/CLAUDE.md"
   fi
   ```

   Do not filter, normalize, or ignore generated sections. If there is any
   difference, stop and ask the user how to resolve it. Never edit only one
   file in a diverged pair.

4. Treat `team-maintainer` as the active default for issue management and
   commits. Agents may manage issues and make atomic commits as work
   progresses unless a current user or orchestrator instruction says
   otherwise.

5. Do **not** push Git branches or sync or push Dolt state unless the current
   user or orchestrator explicitly requests it.

## Enrollment, Repair, and Recovery

For initial enrollment, configuration repair, Beads upgrades, governance-file
changes, or data recovery, read and follow
[Setup and Repair](references/setup.md). Do not load those one-off procedures
for routine Beads work.
