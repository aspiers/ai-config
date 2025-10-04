---
description: Wrapper around /init
allowed-tools: Bash(mv:*), Bash(ln -s:*), Bash(ls:*), Bash(:)
---
# Improve the results of running the /init command

## Goal

`/init` creates `CLAUDE.md`; however this produces results which are only
useful for Claude Code.  To fix this, we want the same file contents to be
discoverable and readable by multiple AI agents looking in different places.

## Context

- Existing files: !`ls CLAUDE.md AGENTS.md GEMINI.md || :`

## Process

Perform the following steps:

1. If neither `CLAUDE.md` nor `AGENTS.md` exists, first perform Claude's `/init`
   process.

2. If `CLAUDE.md` exists, rename to `AGENTS.md`.

3. Generate symlinks `CLAUDE.md`, `AGENT.md`, and `GEMINI.md`, which all point
   to `AGENTS.md`.

This is based on the standard documented at: https://agent-rules.org/
