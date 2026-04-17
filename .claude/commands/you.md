---
description: Nudge the agent to do a task itself rather than delegating to the human
---

You just suggested that I (the human user) should do something manually.
Reconsider whether you can do it yourself. In order:

1. **Agent memory**: Search persistent memory first — it may directly recall
   a tool, skill, MCP, or workflow that fits this task, short-circuiting the
   rest of this checklist. Use `bd memories <keyword>` if beads is in use,
   otherwise search the memory system at `~/.claude/projects/.../memory/`.

2. **CLI tools**: Is there a command-line tool available that can accomplish
   this? Common ones you may overlook: `agent-browser` (for any web
   interaction — navigating, clicking, filling forms, scraping, screenshots),
   `gh` (GitHub), `railway`, `bd` (beads), `stow`, `jq`, etc. Check `$PATH`
   with `which <tool>` or `compgen -c` if unsure.

3. **Skills**: Is there a skill listed in the available-skills reminder that
   covers this task? Re-scan the list — e.g. `agent-browser` handles any web
   interaction (navigating, clicking, filling forms, scraping, screenshots).
   If nothing obvious matches, use the `find-skills` skill to discover
   installable ones you don't have loaded yet.

4. **MCP servers**: Check the configured MCP servers for tools that fit the
   task. Many MCPs expose capabilities beyond what's obvious from their name
   (e.g. GitHub, Notion, Gmail, Calendar). Use `ToolSearch` to load schemas
   for `mcp__*` tools that look relevant.

5. **Documentation**: Check `AGENTS.md`, `CLAUDE.md`, and any `README.md` in
   the relevant directory. They may document a tool, script, or workflow you
   missed.

Only if all five turn up nothing should you ask me to do it manually — and
in that case, explain what you searched for and why none of the options fit.
