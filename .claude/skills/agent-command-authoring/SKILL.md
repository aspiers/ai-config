---
name: agent-command-authoring
description: Create Claude Code slash commands and OpenCode command files that delegate to skills. Use when creating new commands or refactoring existing ones to follow the delegation pattern.
---

# Agent Command Authoring

Create commands that delegate to skills for Claude Code and OpenCode.

## When to Use This Skill

Use this skill when:
- Creating a new custom command
- Refactoring an existing command to delegate to a skill
- Ensuring consistency between Claude Code and OpenCode command implementations

## The Delegation Pattern

Commands should be **thin wrappers** that delegate all implementation to skills:

**Claude Code command** (`.claude/commands/<name>.md`):
```yaml
---
description: Brief description of what the command does
allowed-tools: Skill(skill-name), ...
---

Use the `<skill-name>` skill to accomplish this task.
```

**OpenCode command** (`.config/opencode/command/<name>.md`):
```yaml
---
description: Brief description of what the command does
permission:
  bash:
    ...
---

Use the `<skill-name>` skill to accomplish this task.
```

## Claude Code Command Structure

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | 1-2 sentence description of what the command does |
| `allowed-tools` | Yes | List of tools the command can use, including `Skill(skill-name)` |
| `argument-hint` | No | Hint for command arguments (e.g., `[feature_name [subtask_number]]`) |

### allowed-tools Format

- `Bash(command)` - Allow specific bash command
- `Bash(command:*)` - Allow command with any arguments
- `Read` - Allow reading files
- `Write` - Allow writing files
- `Edit` - Allow editing files
- `Grep` - Allow searching file contents
- `Glob` - Allow finding files by pattern
- `Skill(skill-name)` - Allow loading a skill

**Example:**
```yaml
allowed-tools: Bash(git status:*), Bash(git commit:*), Skill(git-commit)
```

## Naming Conventions

Command names should use the **imperative form** of verbs (telling the agent what to do):

- ✅ `commit`, `stage`, `lint`, `test`, `review`, `reflect`
- ❌ `committing`, `git-committer`, `do-linting`

The imperative form gives commands their characteristic feel:
- "commit" = "perform a commit"
- "stage" = "stage changes"
- "test" = "run tests"

## OpenCode Command Structure

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | 1-2 sentence description of what the command does |
| `permission` | Yes | Map of tool categories to permission rules |

### Permission Format

```yaml
permission:
  bash:
    "git status": "allow"
    "git commit *": "allow"
    "git add *": "deny"
```

Permission values:
- `allow` - Permit without prompting
- `deny` - Always deny
- `ask` - Prompt user each time

## Command Body

The command body should be **5-20 lines maximum** and contain only:

```markdown
Use the `<skill-name>` skill to accomplish this task.
```

**Do NOT include:**
- Full implementation steps
- Duplicated content between Claude and OpenCode
- More than ~20 lines of content

## Examples

### Minimal Command (Claude)

```yaml
---
description: Create well-formatted commits using conventional commits style
allowed-tools: Skill(git-commit)
---

Use the `git-commit` skill to create a well-formatted commit.
```

### Minimal Command (OpenCode)

```yaml
---
description: Create well-formatted commits using conventional commits style
permission:
  bash:
    "git commit *": "allow"
    "git status": "allow"
---

Use the `git-commit` skill to create a well-formatted commit.
```

### Command with Arguments (Claude)

```yaml
---
description: Generate a PRP
argument-hint: [feature_name]
allowed-tools: Skill(prp-generation)
---

Use the `prp-generation` skill to create a Product Requirements Prompt.
```

## Why This Pattern?

1. **Single source of truth**: Skills contain all implementation content
2. **Easier maintenance**: Changes to skills automatically propagate to all commands
3. **Platform consistency**: Commands are thin wrappers with platform-specific frontmatter
4. **Token efficiency**: Skills load progressively via progressive disclosure
5. **No duplication**: Implementation lives in one place

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

**GOOD** - Command that delegates:

```yaml
---
description: Stage changes via git add
allowed-tools: Skill(git-staging)
---

Use the `git-staging` skill to stage relevant changes.
```

## Workflow

1. Create the skill first (or identify existing skill to use)
2. Create/refactor Claude command with proper frontmatter and delegation
3. Create/refactor OpenCode command with matching content and platform-specific frontmatter
4. Verify both commands delegate correctly

## Related Skills

- `subagent-authoring` - For creating subagent definitions that delegate to skills
- `skill-authoring` - For creating skills themselves
