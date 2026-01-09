---
description: Wrapper around /init
permission:
  bash:
    "mv": "allow"
    "ln -s": "allow"
    "ls": "allow"
---
# Improve the results of running the /init command

## Goal

`/init` creates `CLAUDE.md`; however this produces results which are only
useful for Claude Code.  To fix this, we want the same file contents to be
discoverable and readable by multiple AI agents looking in different places.

## Context

- Existing files: !`ls CLAUDE.md AGENTS.md`

## Process

Perform the following steps:

1. If neither `CLAUDE.md` nor `AGENTS.md` exists, first perform Claude's `/init`
   process.

2. If `CLAUDE.md` exists, rename to `AGENTS.md`.

3. Generate symlinks `CLAUDE.md` and `AGENT.md`, which both point
   to `AGENTS.md`.

This is based on the standard documented at: https://agent-rules.org/