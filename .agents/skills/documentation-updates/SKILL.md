---
name: documentation-updates
description: Capture durable project or workflow knowledge discovered during work. Use when a mistake, hidden constraint, repeated question, or changed behavior reveals a documentation gap.
---

# Documentation Updates

Record knowledge where future readers will naturally look for it, without
turning instruction files into a transcript or catch-all memory store.

## Research reports

Store durable research, investigation, audit, and comparison reports under
`docs/research/` relative to the current repository root by default. Defer to a
location specified by the user, the repository, or a focused workflow.

## Workflow

1. Identify the durable lesson and who needs it.
2. Find the authoritative home: nearby code or tests, project documentation,
   an applicable agent rule, a focused skill, or the project's task/memory
   system.
3. Update the smallest relevant source. Link to existing detail rather than
   duplicating it.
4. Check for conflicting or stale guidance and update it in the same scope.
5. Validate examples, commands, links, and any generated or mirrored files.
6. Summarize what changed and why.

## Include

- non-obvious constraints and operational gotchas;
- decisions that remain true beyond the current session;
- reliable recovery or verification procedures; and
- changed user-facing behavior that belongs in product documentation.

## Exclude

- ordinary facts visible from the codebase;
- chronological work logs better suited to issues or comments;
- credentials, personal data, or confidential context;
- speculative rules based on a single unexplained failure; and
- global guidance when the lesson is project-specific.

Do not block unrelated work for a documentation review unless the user asked
for an approval checkpoint or the documentation is required for safe use.
