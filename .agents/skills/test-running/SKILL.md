---
name: test-running
description: Discover and run tests that provide meaningful evidence for a code change. Use after implementation, before handoff or commit, or when the user asks to validate behavior, including checking a desktop, window-manager, keyboard or other GUI change by hand.
---

# Test Running

Choose tests from the behavior and risk of the change, guided by repository
instructions and existing test interfaces.

## Workflow

1. Read applicable project guidance and test configuration.
2. Before running anything broader than unit tests on the user's machine,
   find what the suite touches outside its temporary files: running
   services, sockets under `$XDG_RUNTIME_DIR`, config under `$HOME`,
   ports. Integration tests can take over or delete the live copies the
   user depends on. Point the suite at a scratch location, for example
   `XDG_RUNTIME_DIR=$(mktemp -d)`, after checking the code honours it, or
   skip those tests and report them as skipped. If a documented
   precondition, such as "quit any running daemon first", conflicts with
   your instructions, ask before running. Checking a GUI or desktop change
   by hand counts too: never send synthetic keys or clicks (`xdotool`,
   `ydotool`), grab input devices, or open windows or overlays on the
   user's live display without asking, since they take over the user's
   keyboard and screen. Run it on a nested display, for example `Xephyr
   :1` with `DISPLAY=:1`, or ask the user to try it.
3. Identify the smallest tests that exercise the changed behavior, plus any
   broader gate required by the repository.
4. Run targeted tests early for fast feedback; run required broader tests
   before completion when practical.
5. Diagnose failures before editing. Distinguish product regressions from
   pre-existing failures, flaky behavior, missing services, and environment
   problems.
6. Re-run affected tests after fixes and report commands, scope, and results.

Add or update coverage when the change introduces behavior that the repository
would normally test. Avoid tests that merely mirror implementation details.

## Completion evidence

A passing command is evidence only for the scope it executed. State skipped,
unavailable, flaky, or unrelated failing tests explicitly rather than
reporting an unconditional pass.

Fix failures caused by the current work. For unrelated or infeasible failures,
preserve the evidence and follow repository or user policy on whether they
block completion; do not hide them or redefine warnings as success.
