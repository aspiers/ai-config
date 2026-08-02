---
name: skill-authoring
description: Create and maintain agent skills with concise trigger metadata, judgement-aware guidance, progressive disclosure, and tested interfaces. Use when adding, refactoring, reviewing, or troubleshooting skills and their bundled scripts or references.
---

# Skill Authoring

Build skills that contribute context the model could not reliably infer on its
own. Prefer team or product knowledge, operational gotchas, safety boundaries,
and tested interfaces over generic advice.

## Design principles

### Let the model use judgement

Describe the outcome, relevant constraints, and local conventions. Avoid
absolute workflow rules, arbitrary thresholds, and fixed sequences unless a
safety property, external protocol, or repository policy genuinely requires
them.

When a constraint is necessary, explain the reason and scope so it does not
silently override the user's intent or surrounding project guidance.

### Design interfaces, not exploration paths

For deterministic or fragile work, provide a script or tool with expressive
parameters, useful validation, and actionable errors. Document its contract
and discovery mechanism such as `--help`; do not enumerate every invocation
in `SKILL.md`.

Use examples only when they reveal semantics that the interface cannot express
clearly. Treat examples as illustrations, not templates the model must copy.

### Use progressive disclosure

Skills load in three tiers:

1. Frontmatter advertises what the skill does and when it applies.
2. `SKILL.md` supplies the shortest useful workflow and routing decisions.
3. `references/`, `scripts/`, and `assets/` provide details only when needed.

Keep references one level deep. Link them directly from `SKILL.md` and say when
to read each one. Long API recipes, exhaustive formats, platform-specific
syntax, troubleshooting catalogs, and extended examples usually belong in
references.

### Do not repeat the harness

Do not restate tool schemas, global policies, ordinary coding knowledge, or
instructions already owned by another skill. Link to the owning skill or rely
on the tool description. One rule should have one authoritative home.

### Preserve justified strictness

Low-freedom instructions remain appropriate for destructive actions,
credentials, financial changes, publication, protocol invariants, and other
high-cost failures. Make the boundary narrow and keep the mechanism
verifiable.

## Structure

```text
.agents/skills/<skill-name>/
├── SKILL.md
├── references/   # optional, loaded on demand
├── scripts/      # optional, executable interfaces
└── assets/       # optional, output resources
```

Required frontmatter:

```yaml
---
name: skill-name
description: What the skill does. Use when the relevant trigger occurs.
---
```

- `name` must match the parent directory and follow the Agent Skills
  specification.
- `description` is always-loaded routing context: include capabilities and
  triggers, but not the workflow.
- Use `.agents/skills/` for cross-platform skills unless project guidance says
  otherwise.

## Authoring workflow

1. Identify the non-obvious knowledge or reliable interface the skill adds.
2. Check whether an existing skill, project rule, tool description, or script
   already owns it.
3. Choose the freedom level appropriate to the consequence of error.
4. Write routing metadata, then a concise happy path and decision points.
5. Move conditional or detailed material behind direct reference links.
6. Test scripts and validate frontmatter and links.
7. Re-read the skill and remove repetition, obvious advice, unnecessary
   examples, and constraints that surrounding context can decide better.

## Review questions

- Would a capable model know this without the skill?
- Does each absolute rule protect a real invariant?
- Could a parameterized interface replace prose or examples?
- Is conditional detail loaded only when its condition occurs?
- Does the skill defer to user intent and repository conventions where safe?
- Is another file the authoritative source for any repeated instruction?
- Can a reader discover every referenced file directly from `SKILL.md`?

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Context-engineering principles discussed by Thariq Shams](https://x.com/trq212/status/2080710971228918066)
