# Partial staging with index patches

Use this procedure only when the intended commit includes part of a file.

## Apply a selected patch

Generate the source diff with Git so paths and context match the index:

```bash
git diff --no-ext-diff -- <path> > <temporary-full-patch>
```

Construct a patch containing only the selected changes, then validate and
apply it:

```bash
git apply --cached --check <temporary-selected-patch>
git apply --cached <temporary-selected-patch>
```

`--cached` changes the index without rewriting the working tree.

## Selecting whole hunks

Retain the file headers and only the required `@@ ... @@` sections. A unified
diff needs the `diff --git`, `---`, and `+++` headers for each represented
file. The `index` line is normally safe to retain but is not required for
`git apply --cached`.

## Selecting lines inside a hunk

A hunk header has the form:

```text
@@ -OLD_START,OLD_COUNT +NEW_START,NEW_COUNT @@
```

Counts include context and changed lines on each side.

- To omit an added line, remove its `+` line from the patch.
- To omit a removed line, turn its `-` prefix into a space so it remains
  context.
- Recalculate both counts after editing.
- Preserve the leading space on context lines and any
  `\ No newline at end of file` marker that applies.

When changes are interdependent or the patch would misrepresent the requested
result, stage a larger coherent unit or ask the user to choose the boundary.

## Verification and recovery

After applying, inspect both diffs:

```bash
git diff --cached --no-ext-diff
git diff --no-ext-diff
git status --short
```

If validation fails, regenerate the source diff from the current index rather
than repeatedly weakening context. `patch does not apply` usually means the
index changed, context was removed, or hunk counts are wrong. Use
`git apply --cached --verbose` for diagnostics only after `--check` has
reproduced the failure.
