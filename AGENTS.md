# AGENTS.md

## Context

- This repository contains configs for AI agents such as Claude Code, OpenCode
  etc., as well as associated shell scripts and other utility files.

- **⚠️ THIS REPOSITORY IS PUBLIC.** Its skills and configs are published for
  consumption by people other than the author. Read "Public repository — no
  private or sensitive content" below BEFORE adding or editing anything.

- Editorconfig: @.editorconfig

## Public repository — no private or sensitive content

**This repo is PUBLIC and its skills are used by other people.** Anything
committed here is world-readable, permanently, via the git history —
deleting it later does NOT unpublish it.

### NEVER commit sensitive content

Not in any file, not in an example, not in a "temporary" note:

- **Credentials** — API keys, tokens, bearer tokens, passwords, OAuth client
  secrets, session cookies, private keys, `.env` contents
- **Personal data** — home/email addresses, phone numbers, bank account or
  card numbers (including partial/masked digits)
- **Financial data** — balances, transaction amounts, supplier relationships,
  invoice/bill references, tax positions, capitalisation thresholds
- **Identifiers that resolve to real records** — Xero/Hubdoc organisation,
  contact, invoice, account or document IDs; real UUIDs from live systems
- Anything under a confidentiality obligation

If a credential ever does land here, treat it as **compromised**: rotate it,
don't merely delete it.

### Author-specific facts need a CLEAR WARNING, or they don't belong

A skill must be **useful and correct for a stranger**. Content that only
applies to the author's own setup is a defect unless clearly marked.

Prefer, in order:

1. **Generalise it.** Describe the mechanism, not the author's instance:
   "consult your organisation's account-code conventions" — not a table of
   the author's suppliers and codes.
2. **Point at a kind of location, not at contents.** "conventions may live in
   a notes file, `$ACCOUNTING_NOTES`, or a project CLAUDE.md" — never inline
   a personal absolute path as though it were universal.
3. **If it genuinely must be specific, MARK IT LOUDLY** and scope it:

   > **⚠️ AUTHOR-SPECIFIC:** the following applies to the author's own setup.
   > Substitute your own conventions.

Otherwise a reader silently inherits someone else's accounting rules,
supplier list, or card numbers as though they were general truth — wrong for
them, and a leak by the author.

### Private/author-specific material belongs elsewhere

Put it in a **private repo** (e.g. the relevant project's own
`.claude/skills/`), in agent memory, or in the issue tracker — not here.
Project-level skills in a private repo are the right home for
organisation-specific conventions.

**Evidence (2026-07-17):** an agent editing a skill in this repo inlined the
author's personal notes path, a table of the author's real suppliers mapped
to account codes, the author's capitalisation threshold, and the name of the
author's accountancy firm — plus an adviser lock date in another skill. None
of it was useful to anyone else, and the author had to catch it. AGENTS.md
gave no indication the repo was public, which is why this section exists.

## Adding/Changing Allowed Commands

Use the `allow-agent-commands` skill for instructions on adding or modifying
command permissions in AI agent configs.

## Git Operations

For `git diff` commands, always use `git diff --no-ext-diff`. (N.B. The flag
has to come after `diff`.)

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

**Official specification**: <https://agentskills.io/specification>

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

Use the repository's deployment workflow to manage skills that should be
available globally.

> **⚠️ AUTHOR-SPECIFIC:** In the maintainer's checkout, run `mr stow` for
> deployment. Do not invoke GNU Stow directly; `mr` selects and wraps the
> stowable packages. Other users should substitute their own deployment
> workflow.

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

See <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
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
| ---------- | --------- |
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

## Beads Solo

Use the `beads-solo` skill for Beads setup and maintainer policy in this
repository. Use the `beads` skill for the standard Beads workflow.

This repository opts into the Beads **team-maintainer** profile for issue
management and commits. Unless a current user or orchestrator instruction
says otherwise, agents may manage issues and make atomic commits as work
progresses. They must not push Git branches or sync or push Dolt state unless
explicitly requested.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See <https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md> for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:

   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```

5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**

- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

<!-- BEGIN BEADS CODEX SETUP: generated by bd setup codex -->
## Beads Issue Tracker

Use Beads (`bd`) for durable task tracking in repositories that include it. Use the `beads` skill at `.agents/skills/beads/SKILL.md` (project install) or `~/.agents/skills/beads/SKILL.md` (global install) for Beads workflow guidance, then use the `bd` CLI for issue operations.

### Quick Reference

```bash
bd ready                # Find available work
bd show <id>            # View issue details
bd update <id> --claim  # Claim work
bd close <id>           # Complete work
bd prime                # Refresh Beads context
```

### Rules

- Use `bd` for all task tracking; do not create markdown TODO lists.
- Run `bd prime` when Beads context is missing or stale. Codex 0.129.0+ can load Beads context automatically through native hooks; use `/hooks` to inspect or toggle them.
- Keep persistent project memory in Beads via `bd remember`; do not create ad hoc memory files.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See <https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md> for details and anti-patterns.
<!-- END BEADS CODEX SETUP -->
