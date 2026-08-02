---
name: project-initialization
description: Establish concise, cross-agent project instructions from repository evidence. Use when initializing or repairing AGENTS.md, CLAUDE.md, related discovery links, or project-specific agent guidance.
---

# Project Initialization

Create a lightweight entry point that explains the repository and highlights
non-obvious gotchas. Do not turn it into a catalog of generic development
advice.

## Workflow

1. Inspect existing agent instructions, repository documentation, build and
   test interfaces, and file-discovery conventions supported by the target
   harnesses.
2. Preserve useful existing guidance and identify conflicts before editing.
3. Choose one authoritative instruction file when the repository wants shared
   content. Use symlinks or small platform-specific entry points only when they
   are supported by the repository and tools; do not rename files or replace
   independent guidance without agreement.
4. Keep the entry point concise:
   - what the repository is;
   - authoritative build, test, and validation commands;
   - architecture or workflow facts that are not obvious from the tree; and
   - narrow safety or contribution constraints.
5. Move detailed or conditional workflows into focused skills or directly
   linked documentation.
6. Verify every discovery path, symlink, command, and cross-reference.

## Safety review

Review generated instructions for commands that could publish, delete,
overwrite, migrate, or expose data. Prefer explicit targets and narrow scope,
but preserve intentional repository workflows rather than rewriting commands
from a universal template.

Do not add secrets, personal conventions, or private operational details to a
public repository. Avoid duplicating global harness rules or facts the model
can obtain by inspecting the project.

## Result

Report the authoritative file, compatibility links or wrappers, validation
performed, and any platform whose discovery behavior remains uncertain.
