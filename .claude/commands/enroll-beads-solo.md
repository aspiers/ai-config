---
description: Enroll this repository in the beads-solo maintainer profile
argument-hint: "[local] [prefix=<prefix>] [other details]"
allowed-tools: Skill(beads-solo), Bash(bd-enroll-solo:*)
---

The user explicitly requests enrollment of the current repository in the
beads-solo maintainer profile. This message is the explicit user approval
that the `beads-solo` skill requires before creating an enrollment.

Arguments: $ARGUMENTS

Use the `beads-solo` skill and follow its Setup and Repair reference. Read
the arguments as enrollment options:

- `local` selects the local profile (`bd-enroll-solo --local`). Without it,
  use the tracked profile, but confirm the profile first if it is not obvious
  that the user owns the repository.
- A prefix such as `prefix=foo` or `--prefix foo` is passed through as
  `--prefix`. Without one, present the default prefix and confirm it before
  enrolling, since it becomes a permanent part of every issue ID.
- Treat anything else as context for the enrollment.

Show the user the `--dry-run` output first, then run the enrollment with
`--yes` once they approve. Do not perform the steps by hand.
