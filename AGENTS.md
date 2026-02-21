# AGENTS.md

## Context

- This repository contains configs for AI agents such as Claude Code, OpenCode
  etc., as well as associated shell scripts and other utility files.

- Editorconfig: @.editorconfig

## Adding/Changing Allowed Commands

Use the `allow-agent-commands` skill for instructions on adding or modifying
command permissions in AI agent configs.

## Git Operations

For git commands, always use `--no-ext-diff` flag with `git diff`.

If you've recently made a commit in a local branch that hasn't been published
anywhere else yet and then you notice a mistake in it, in order to avoid
polluting the history with a bunch of mistakes and fixups, you should
*generally* prefer amending that commit over adding a fixup on top.  But this
is ONLY OK if the amended result remains a single logical change!  Commits
must NOT combine unrelated changes!

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

**Project-specific skills** (preferred, cross-platform): `.agents/skills/<skill-name>/SKILL.md`
**Global skills** (preferred, cross-platform): `~/.agents/skills/<skill-name>/SKILL.md`

`.agents/skills/` is the emerging cross-platform standard supported by Claude
Code, OpenCode, and other agents. `.claude/skills/` is also still scanned for
backwards compatibility.

Use stow or symlinks to manage skills in this repository that should be
available globally.

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

Location: `.agents/skills/safe-rm/SKILL.md`

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

## Available Subagents

Subagents are specialized AI agents that delegate to skills. They follow the naming
convention of **agent nouns** with the **-er suffix** ("one who does X"):

| Subagent | Purpose |
|----------|---------|
| `code-deduplicator` | Remove code duplication |
| `code-linter` | Run linters |
| `code-refactorer` | Refactor large code units |
| `code-reviewer` | Review code for quality |
| `doc-updater` | Update documentation |
| `git-committer` | Create commits |
| `git-stager` | Stage changes |
| `pr-describer` | Generate PR descriptions |
| `prp-generator` | Generate PRPs |
| `task-generator` | Generate tasks from PRPs |
| `task-implementer` | Implement tasks |
| `task-orchestrator` | Orchestrate complete workflow |
| `test-runner` | Run tests |

See `.claude/agents/` for the full definitions.

## Command and Agent Delegation Pattern

All custom commands and subagent definitions should delegate to skills rather
than containing implementation content directly.

### The Pattern

**Commands** (`.claude/commands/<name>.md` and `.config/opencode/command/<name>.md`):

```yaml
---
description: Brief description of what the command does
allowed-tools: Skill(skill-name), ...
---

Use the `<skill-name>` skill to accomplish this task.
```

**Agents** (`.claude/agents/<name>.md` and `.config/opencode/agents/<name>.md`):

```yaml
---
name: agent-name
description: Brief description of what the agent does
tools: Read, Grep, Glob, Skill(skill-name), ...
---

Use the `<skill-name>` skill to accomplish this task.
```

### Why This Pattern?

1. **Single source of truth**: Skills contain all implementation content
2. **Easier maintenance**: Changes to skills automatically propagate
3. **Platform consistency**: Commands/agents are thin wrappers with platform-specific frontmatter
4. **Token efficiency**: Agents load skills progressively via progressive disclosure

### Anti-Pattern to Avoid

Commands or agents with:
- Full implementation steps beyond "Use the X skill"
- Duplicated content between Claude and OpenCode versions
- More than ~20 lines of content beyond frontmatter and delegation instruction

## Verification Commands

- **Shell scripts**: `bash -n script`
- **JSON files**: `jq . file.json >/dev/null`
- **Python tests**: `python3 tests/test_*.py`

**Always run tests and verification commands before completing any code change.**

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
