# AGENTS.md

## Context

- This repository contains configs for AI agents such as Claude Code, OpenCode
  etc., as well as associated shell scripts and other utility files.

- Editorconfig: @.editorconfig

## Adding/Changing Allowed Commands

Commands must be explicitly allowed in the permission configs before agents
can run them. Add entries in the appropriate config file:

### OpenCode

File: `.config/opencode/opencode.json` under `permission.bash`

Format:
```json
"uname *": "allow",
```

Pattern: `"command argpatterns": "action"` where `*` matches any args

### Claude Code

File: `.claude/settings.json` under `permissions.allow`

Format:
```json
"Bash(uname:*)",
```

### General Pattern

When adding new AI tools:

1. Find their config file (usually in `~/.config/` or project root)
2. Look for `permissions`, `allowedCommands`, or similar sections
3. Add the command with glob patterns for arguments

## Git Operations

For git commands, always use `--no-ext-diff` flag with `git diff`.

## Verification Commands

- **Shell scripts**: `bash -n script`
- **JSON files**: `jq . file.json >/dev/null`
