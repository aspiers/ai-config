---
name: agent-command-authoring
description: Create Claude Code slash commands, OpenCode command files, and Pi prompt templates that delegate to the right subagent or skill. Use when creating new commands or refactoring existing ones to follow platform conventions.
---

# Agent Command Authoring

Create commands for Claude Code, OpenCode, and Pi that are thin wrappers around
reusable agent capabilities.

## When to Use This Skill

Use this skill when:
- Creating a new custom command
- Refactoring an existing command to delegate correctly
- Porting commands between Claude Code, OpenCode, and Pi
- Ensuring consistency between command implementations across agent harnesses

## Platform Model

Different harnesses support different delegation mechanisms:

| Platform | Command location | Preferred delegation |
|----------|------------------|----------------------|
| Claude Code | `.claude/commands/<name>.md` | `Task(subagent-name)` for context-independent tasks; `Skill(skill-name)` for session-context-dependent tasks |
| OpenCode | `.config/opencode/command/<name>.md` | `agent: subagent-name` for context-independent tasks; omit `agent:` and call the skill directly for session-context-dependent tasks |
| Pi | `.pi/prompts/<name>.md` project-local, or `~/.pi/agent/prompts/<name>.md` global | Prompt template that invokes the skill directly |

Pi does **not** have subagents by default, so Pi command templates should not
reference `Task(...)`, `agent:`, or "use the `<name>` subagent". Convert those
to direct skill invocation.

## The Delegation Pattern

For Claude Code and OpenCode, commands should usually be **thin wrappers** that
delegate to subagents, which in turn delegate to skills:

```
command → subagent → skill
```

For Pi, commands are prompt templates and should invoke skills directly:

```
prompt template → skill
```

## Claude Code Command Structure

**Claude Code command** (`.claude/commands/<name>.md`):

```yaml
---
description: Brief description of what the command does
allowed-tools: Task(subagent-name)
---

Use the `<subagent-name>` subagent to accomplish this task.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | 1-2 sentence description of what the command does |
| `allowed-tools` | Yes for subagent commands | `Task(subagent-name)` to invoke the subagent |
| `argument-hint` | No | Hint for command arguments (e.g., `[feature_name [subtask_number]]`) |

### `allowed-tools` Format

For commands that delegate to subagents:
- `Task(subagent-name)` - Invoke a subagent

For commands that must run in the current session context:
- `Skill(skill-name)` - Invoke the skill directly

**Example:**

```yaml
allowed-tools: Task(git-committer)
```

## OpenCode Command Structure

**OpenCode command** (`.config/opencode/command/<name>.md`):

```yaml
---
description: Brief description of what the command does
agent: <subagent-name>
---

Use the `<subagent-name>` subagent to accomplish this task.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | 1-2 sentence description of what the command does |
| `agent` | Yes for subagent commands | Name of the subagent to invoke |
| `argument-hint` | No | Hint for command arguments |

For session-context-dependent commands, omit `agent:` so the command runs in
the primary agent's context, and invoke the skill directly in the body.

## Pi Prompt Template Structure

**Pi prompt template** (`.pi/prompts/<name>.md` or `~/.pi/agent/prompts/<name>.md`):

```yaml
---
description: Brief description of what the command does
argument-hint: "[optional-args]"
---

Use the `<skill-name>` skill to accomplish this task.

Arguments: $ARGUMENTS
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | No, but recommended | Description shown in `/` autocomplete |
| `argument-hint` | No | Hint shown before the description in autocomplete |

### Pi Rules

- Filename becomes the slash command: `.pi/prompts/review.md` creates `/review`.
- Use `$1`, `$2`, `$@`, or `$ARGUMENTS` for arguments.
- Do not include Claude/OpenCode-only fields: `allowed-tools`, `agent`, `model`,
  `mode`, `permission`, or `tools`.
- Do not reference subagents unless a Pi extension/package explicitly provides
  them. Prefer direct skill invocation.
- After adding or changing templates in a running Pi session, run `/reload`.

### Common Subagent → Skill Mapping for Pi

When porting existing Claude/OpenCode commands to Pi, map common subagents to
skills:

| Subagent | Pi skill |
|----------|----------|
| `git-committer` | `git-commit` |
| `git-stager` | `git-staging` |
| `code-linter` | `code-linting` |
| `test-runner` | `test-running` |
| `pr-describer` | `describing-prs` |
| `prp-generator` | `prp-generation` |
| `task-generator` | `task-generation` |

## Naming Conventions

Command names should use the **imperative form** of verbs (telling the agent what to do):

- ✅ `commit`, `stage`, `lint`, `test`, `review`, `reflect`
- ❌ `committing`, `git-committer`, `do-linting`

The imperative form gives commands their characteristic feel:
- "commit" = "perform a commit"
- "stage" = "stage changes"
- "test" = "run tests"

## Command Body

The command body should be **5-20 lines maximum** and contain only delegation
and argument-passing instructions.

**Claude/OpenCode subagent command:**

```markdown
Use the `<subagent-name>` subagent to accomplish this task.
```

**Pi prompt template or direct-skill command:**

```markdown
Use the `<skill-name>` skill to accomplish this task.

Arguments: $ARGUMENTS
```

**Do NOT include:**
- Full implementation steps
- Duplicated content between command wrappers
- More than ~20 lines of content
- Platform-specific frontmatter in the wrong platform's command file

## Examples

### Minimal Command (Claude Code)

```yaml
---
description: Create well-formatted commits using conventional commits style
allowed-tools: Task(git-committer)
---

Use the `git-committer` subagent to create a well-formatted commit.
```

### Minimal Command (OpenCode)

```yaml
---
description: Create well-formatted commits using conventional commits style
agent: git-committer
---

Use the `git-committer` subagent to create a well-formatted commit.
```

### Minimal Command (Pi)

```yaml
---
description: Create well-formatted commits using conventional commits style
---

Use the `git-commit` skill to create a well-formatted commit.
```

### Command with Arguments (Claude Code)

```yaml
---
description: Generate a PRP
argument-hint: [feature_name]
allowed-tools: Task(prp-generator)
---

Use the `prp-generator` subagent to create a Product Requirements Prompt.
```

### Command with Arguments (Pi)

```yaml
---
description: Generate a PRP
argument-hint: "[feature_name]"
---

Use the `prp-generation` skill to create a Product Requirements Prompt.

Feature: $ARGUMENTS
```

## Why This Pattern?

1. **Single source of truth**: Skills contain all implementation content
2. **Easier maintenance**: Changes to skills automatically propagate
3. **Platform consistency**: Commands are thin wrappers with platform-specific frontmatter
4. **Token efficiency**: Skills load progressively via progressive disclosure
5. **No duplication**: Implementation lives in one place (the skill)
6. **Isolation where available**: Claude/OpenCode subagents run context-independent tasks in their own context
7. **Pi compatibility**: Pi prompt templates preserve slash-command ergonomics without assuming subagents

## Anti-Pattern to Avoid

**BAD** - Command with full implementation:

```yaml
---
description: Stage changes
allowed-tools: Bash(git add:*)
---

# Staging Changes

Stage relevant changes via `git add`...

1. Run `git status` to check for already staged changes
2. Verify no staged changes exist...
3. Run `git status` again...
4. Carefully review which files are relevant...
5. Stage only the relevant files...
6. Run `git status` again...
```

**BAD for Pi** - Pi template that references a subagent:

```yaml
---
description: Stage changes via git add
---

Use the `git-stager` subagent to stage relevant changes.
```

**GOOD for Pi** - Pi template that invokes the skill directly:

```yaml
---
description: Stage changes via git add
---

Use the `git-staging` skill to stage relevant changes.
```

**BAD for Claude/OpenCode** - Command that delegates directly to skill for a
context-independent task when a subagent exists:

```yaml
---
description: Stage changes via git add
allowed-tools: Skill(git-staging)
---

Use the `git-staging` skill to stage relevant changes.
```

**GOOD for Claude/OpenCode** - Command that delegates to subagent for a
context-independent task:

```yaml
---
description: Stage changes via git add
allowed-tools: Task(git-stager)
---

Use the `git-stager` subagent to stage relevant changes.
```

**EXCEPTION** - Commands that are inherently session-context-dependent (e.g.
"review what I just wrote", "remove duplication I just introduced") should
skip the subagent and invoke the skill directly. Subagents start with a fresh
context and will not know what was recently worked on unless the parent agent
tells them — which defeats the purpose of the command.

```yaml
---
description: Remove code duplication you just introduced
allowed-tools: Skill(code-refactoring-dry)
---

Use the `code-refactoring-dry` skill to remove duplication in the files you
have worked on in this session.
```

In OpenCode, omit the `agent:` field entirely for the same effect. In Pi, all
prompt templates should use this direct skill-invocation style.

## Workflow

1. **Check for existing skill**: Identify the skill the command should use.
2. **For Claude/OpenCode context-independent commands**: Check for an existing
   subagent that delegates to that skill:
   - Claude Code: `.claude/agents/<name>.md`
   - OpenCode: `.config/opencode/agents/<name>.md`
3. **If no subagent exists for Claude/OpenCode**: Ask the user if they want one created.
   - If yes, use the `subagent-authoring` skill to create it first.
   - If no, create only the Pi template or stop and explain the limitation.
4. Create/refactor Claude Code command with `allowed-tools: Task(subagent-name)`.
5. Create/refactor OpenCode command with `agent: subagent-name`.
6. Create/refactor Pi prompt template with direct skill invocation in `.pi/prompts/<name>.md`.
7. Verify the chains:
   - Claude/OpenCode: command → subagent → skill
   - Pi: prompt template → skill

## Missing Subagent Handling

Before creating a Claude/OpenCode subagent command, always verify the target
subagent exists:

```bash
# Check Claude Code subagent
ls ~/.claude/agents/<subagent-name>.md

# Check OpenCode subagent
ls ~/.config/opencode/agents/<subagent-name>.md
```

If either file is missing, **ask the user**:

> "The subagent `<subagent-name>` doesn't exist yet. Would you like me to
> create it using the `subagent-authoring` skill before proceeding with
> the Claude/OpenCode command?"

Do NOT create Claude/OpenCode commands that reference non-existent subagents.
This requirement does not apply to Pi prompt templates, which should reference
skills directly.

## Verification

After creating or refactoring commands:

```bash
# YAML/frontmatter sanity check for generated markdown files
python3 - <<'PY'
from pathlib import Path
import yaml
for root in ['.claude/commands', '.config/opencode/command', '.pi/prompts']:
    for path in Path(root).glob('*.md'):
        text = path.read_text()
        if text.startswith('---\n'):
            yaml.safe_load(text.split('---', 2)[1])
print('command frontmatter ok')
PY
```

For Pi, also check that templates do not contain Claude/OpenCode-only fields:

```bash
grep -RIn 'allowed-tools\|^agent:\|Task(\|subagent' .pi/prompts || true
```

Run `/reload` in active Pi sessions after changing Pi prompt templates.

## Related Skills

- `subagent-authoring` - For creating Claude/OpenCode subagent definitions that delegate to skills
- `skill-authoring` - For creating skills themselves
