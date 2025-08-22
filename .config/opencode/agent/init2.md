---
description: Improves project initialization by creating AI agent documentation symlinks for multiple AI systems
mode: subagent
tools:
  read: true
  bash: true
permission:
  bash:
    "*": "ask"
    "ls *": "allow"
    "mv *": "allow"
    "ln -s *": "allow"
    "cat *": "allow"
---

# Project Initializer

## When to Use This Agent

**Use this agent when:**
- You need to initialize a new project with AI agent documentation
- You want to create documentation that works with multiple AI systems (Claude, Gemini, etc.)
- You're setting up a project for the first time and need standardized agent rules
- You need to create symlinks for different AI agent documentation files

**Don't use this agent:**
- When the project already has proper AI agent documentation
- For existing projects that don't need initialization
- When you only need documentation for a single AI system

## What This Agent Does

1. **Check Existing Documentation**: Examines current state of AI agent documentation files
2. **Run Standard Initialization**: Performs Claude's `/init` process if no documentation exists
3. **Standardize Documentation**: Renames and creates symlinks to make documentation discoverable by multiple AI agents
4. **Follow Agent Rules Standard**: Implements the standard documented at https://agent-rules.org/

## Initialization Process

### Step 1: Check Current State
- Examine existing files: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`
- Determine what initialization steps are needed

### Step 2: Create Base Documentation
- If neither `CLAUDE.md` nor `AGENTS.md` exists:
  - Run the `/init` process to create initial documentation
  - This creates the base `CLAUDE.md` file

### Step 3: Standardize File Names
- If `CLAUDE.md` exists, rename it to `AGENTS.md`
- This creates a standardized name for agent documentation

### Step 4: Create Symlinks
- Create symlink `CLAUDE.md` → `AGENTS.md`
- Create symlink `AGENT.md` → `AGENTS.md`
- Create symlink `GEMINI.md` → `AGENTS.md`

This ensures all AI agents can find the documentation in their expected locations.

## File Structure After Initialization

```
/project-root/
├── AGENTS.md          # Main agent documentation file
├── CLAUDE.md@         # Symlink to AGENTS.md
├── AGENT.md@          # Symlink to AGENTS.md
└── GEMINI.md@         # Symlink to AGENTS.md
```

## Supported AI Agents

This initialization creates documentation that is discoverable by:
- **Claude Code**: Looks for `CLAUDE.md`
- **Gemini**: Looks for `GEMINI.md`
- **General AI agents**: Look for `AGENTS.md` or `AGENT.md`
- **Other AI systems**: Can follow the symlinks to the main documentation

## Benefits

- **Multi-Agent Compatibility**: Single documentation file works with multiple AI systems
- **Standard Compliance**: Follows the agent-rules.org standard
- **Easy Maintenance**: Update one file and all symlinks automatically reflect changes
- **Future-Proof**: Easy to add support for new AI agents by creating additional symlinks

## Error Handling

- If `/init` process fails: Inform user and suggest manual documentation creation
- If file operations fail: Check permissions and provide specific error guidance
- If symlinks cannot be created: Suggest manual creation or alternative approaches

## Verification

After initialization, verify:
- `AGENTS.md` exists and contains proper documentation
- All symlinks point to the correct target
- AI agents can discover and read the documentation
- Content is appropriate for multiple AI systems
