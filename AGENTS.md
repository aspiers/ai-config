# AGENTS.md

## Context

- This repository contains configs for AI agents such as Claude Code, OpenCode
  etc., as well as associated shell scripts and other utility files.

- Editorconfig: @.editorconfig

## Adding/Changing Allowed Commands

Use the `allow-commands` skill for instructions on adding or modifying
command permissions in AI agent configs.

## Git Operations

For git commands, always use `--no-ext-diff` flag with `git diff`.

## Adding Agent Skills

Agent Skills are modular packages that extend AI agent capabilities by
bundling instructions, scripts, and resources. They work across multiple
platforms including Claude Code, OpenCode, Cursor, Amp, Letta, Goose,
GitHub Copilot, VS Code, and Claude.ai.

**Official specification**: https://agentskills.io/specification

### Skill Structure

Every skill is a directory containing a `SKILL.md` file with:

1. **YAML Frontmatter (required)**:
   ```yaml
   ---
   name: skill-name
   description: Brief description of what the skill does and when to use it
   ---
   ```

   **Required fields**:
   - `name`: 1-64 chars, lowercase alphanumeric and hyphens only, cannot
     start/end with hyphen or contain consecutive hyphens. Must match
     parent directory name.
   - `description`: 1-1024 chars describing what the skill does and when
     to use it, including keywords to help agents identify relevant tasks.

   **Optional fields**:
   - `compatibility`: Environment requirements (1-500 chars)
   - `metadata`: String key-value mapping for additional properties
   - `allowed-tools`: Space-delimited list of pre-approved tools
     (experimental)

2. **Instructions**: Markdown content explaining how to use the skill
   (recommended <500 lines, <5000 tokens)

3. **Optional directories**:
   - `scripts/`: Executable code (Python, Bash, JavaScript)
   - `references/`: Additional documentation loaded on demand
   - `assets/`: Static resources (templates, images, data)

### Progressive Disclosure

Skills use a three-level information architecture:

1. **Level 1**: Name and description (loaded at startup in system prompt)
2. **Level 2**: Complete SKILL.md content (loaded when relevant)
3. **Level 3**: Referenced files (accessed only when needed)

This keeps token usage efficient while maintaining full capability.

### Location

**Project-specific skills**: `.claude/skills/<skill-name>/SKILL.md`
**Global skills**: `~/.claude/skills/<skill-name>/SKILL.md`

Both Claude Code and OpenCode automatically scan `~/.claude/skills/` for
global skills. Use stow or symlinks to manage skills in this repository
that should be available globally.

### Integration with Helper Scripts

Skills commonly reference helper scripts (bash, python) stored in `bin/`
or similar directories. The skill's SKILL.md should:

- Document what the script does
- Explain when the agent should call it
- Clarify permission requirements (if any)

Example:

```markdown
## Usage

When you need to delete files safely:

1. Identify the files to delete
2. Call `ai-safe-rm <file1> <file2> ...`
3. The script will handle git-aware backup logic
```

### Best Practices

See https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
for a full description.  Short summary:

- Keep SKILL.md concise; use referenced files for detailed docs
- Include examples showing when to use the skill
- Explain any pre-requisites or dependencies
- Document behavior differences across platforms if applicable
- Use helper scripts for deterministic operations (avoid token-heavy tasks)

### Example Skill: safe-rm

Location: `.claude/skills/safe-rm/SKILL.md`

This skill demonstrates best practices for structure and documentation:

```yaml
---
name: safe-rm
description: Safely delete files / directories without asking for permission
---

# Safe File Deletion

## When to use this skill

Whenever deletion of files or directories is required...

## How it works

It runs the `ai-safe-rm` script which has an intelligent git-aware
backup strategy.

## Behavior

The `ai-safe-rm` script handles three cases:
1. Tracked in git, unmodified: delete directly
2. Tracked in git, modified: backup to `.safe-rm/`
3. Not tracked in git: backup to `.safe-rm/`

## Usage

1. Identify the files to delete
2. Call `ai-safe-rm <file1> <file2> ...`
3. Review the output

## Examples

```bash
ai-safe-rm src/old-component.ts
ai-safe-rm src/legacy/*.js
```
```

**Key structural elements:**
- Clear "When to use" section helps agent recognize relevance
- "How it works" provides high-level overview
- "Behavior" explains the logic
- "Usage" gives step-by-step process
- "Examples" show concrete use cases

Helper script: `bin/ai-safe-rm`

## Testing

Test suites are located in the `tests/` directory.

### Running tests

```bash
# Run all tests for ai-safe-rm
python3 tests/test_ai_safe_rm.py

# Run with verbose output
python3 tests/test_ai_safe_rm.py -v

# Run specific test
python3 tests/test_ai_safe_rm.py TestAiSafeRm.test_modified_tracked_file_backed_up
```

See `tests/README.md` for detailed test documentation.

## Verification Commands

- **Shell scripts**: `bash -n script`
- **JSON files**: `jq . file.json >/dev/null`
- **Python tests**: `python3 tests/test_*.py`

**Always run tests and verification commands before completing any code change.**
