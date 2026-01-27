---
description: Add or change allowed commands in AI agent permission configs
allowed-tools: Skill(allow-agent-commands)
---

Use the `allow-agent-commands` skill to add the specified command to both OpenCode and Claude Code permission configs.

**IMPORTANT**: The entire argument string after `/allow` is a SINGLE command (including any subcommands and spaces). For example:
- `/allow bd dep` means allow the command "bd dep"
- `/allow npm run build` means allow the command "npm run build"
- `/allow git commit -m` means allow the command "git commit -m"

Do NOT treat the arguments as separate commands to allow.
