---
name: git-staging
description: Stage whole files, selected hunks, or selected lines in Git without interactive prompts. Use when preparing an exact commit boundary while preserving unrelated working-tree changes.
---

# Non-interactive Git Staging

Stage only the changes intended for the next commit. The index is shared state:
preserve anything already staged unless the user explicitly asks to replace
or unstage it.

## Workflow

1. Inspect all three states:

   ```bash
   git status --short
   git diff --no-ext-diff
   git diff --cached --no-ext-diff
   ```

2. Derive the desired commit boundary from the user's request and the diff.
   Group by logical purpose rather than file count.
3. Choose the least complex safe operation:
   - complete file: `git add -- <path>`;
   - part of a file: construct a patch and apply it to the index;
   - ambiguous overlap with existing staged work: stop and clarify.
4. Verify both sides of the boundary:

   ```bash
   git diff --cached --no-ext-diff
   git diff --no-ext-diff
   git status --short
   ```

A successful `git add` or `git apply` is not sufficient evidence; the staged
diff must contain the intended change and exclude unrelated work.

## Partial staging

For selected hunks or lines, read
[Partial staging with index patches](references/partial-staging.md) before
constructing the patch. It contains the patch rules, validation sequence, and
failure recovery. Do not use interactive `git add -p` in a non-interactive
agent session.

## Safety

- Use `--` before paths that could be parsed as options.
- Do not discard working-tree content as part of staging.
- Do not use broad commands such as `git add .` when unrelated changes are
  present or the requested boundary is narrower.
- Keep temporary patches in a repository-approved ignored location and remove
  them when no longer needed.
