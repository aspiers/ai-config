---
description: "Nudge the agent to do a task itself rather than delegating to the human"
---

You just suggested that I (the human user) should do something manually.
Reconsider whether you can do it yourself. In order:

1. **Agent memory**: Search persistent memory first. It may directly recall a
   tool, skill, MCP, or workflow that fits this task. Use
   `bd memories <keyword>` if Beads is in use; otherwise use the current
   agent's memory facilities.

2. **CLI tools**: Is there a command-line tool available that can accomplish
   this? Common ones you may overlook: `agent-browser` (for any web
   interaction — navigating, clicking, filling forms, scraping, screenshots),
   `gh` (GitHub), `railway`, `bd` (beads), `stow`, `jq`, etc. Check `$PATH`
   with `which <tool>` or `compgen -c` if unsure.

3. **Skills**: Is there a skill listed in the available-skills reminder that
   covers this task? Re-scan the list. For example, `agent-browser` handles web
   interaction such as navigating, clicking, filling forms, scraping, and
   screenshots.
   If nothing obvious matches, use the `find-skills` skill to discover
   installable ones you don't have loaded yet.

4. **MCP servers**: Check the configured MCP servers for tools that fit the
   task. Many MCPs expose capabilities beyond what's obvious from their name,
   such as GitHub, Notion, Gmail, and Calendar. Use the current agent's tool
   discovery facility to load schemas for relevant MCP tools.

5. **Documentation**: Check `AGENTS.md`, `CLAUDE.md`, and any `README.md` in
   the relevant directory. They may document a tool, script, or workflow you
   missed.

Only if all five turn up nothing should you ask me to do it manually. Explain
what you searched for and why none of the options fit.
