# Global rules audit (2026-09-30)

Audit of `.claude/CLAUDE.md` (7,858 B, 163 lines) while moving its rules
into the shared `.agents/AGENTS.md` (draft: 2,777 B, 57 lines) for bead
`ai-vtq`. Verdicts: **keep** (move as is, condensed), **generalise** (merge
or make harness-neutral), **drop**.

## Basis

- Anthropic's prompting guide says newer models are "more responsive to the
  system prompt" and may overtrigger: "The fix is to dial back any
  aggressive language. Where you might have said 'CRITICAL: You MUST use
  this tool when...', you can use more normal prompting".
  <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>
- Claude Code docs: "target under 200 lines per CLAUDE.md file. Longer
  files consume more context and reduce adherence", and "if two
  instructions contradict each other, Claude may pick one arbitrarily".
  <https://code.claude.com/docs/en/memory#write-effective-instructions>
- Codex reads a limited byte budget across all `AGENTS.md` files, so every
  byte in the global file is taken from project instructions.

## Verdicts

| # | Rule | Verdict | Reason |
| - | ---- | ------- | ------ |
| 1 | "ALL rules MANDATORY" header, CRITICAL/AGAIN emphasis | drop | Aggressive emphasis overtriggers on current models (guide above) |
| 2 | `@.editorconfig` import | drop | Resolves to `~/.claude/.editorconfig`, which does not exist; dead |
| 3 | No guessing, verify assumptions, state assumptions, avoid speculation | generalise | Four overlapping bullets merged into two |
| 4 | Consult official docs first (cost order) | generalise | Merged into 3; "WebFetch" made tool-neutral |
| 5 | Re-pick approach on new information | keep | Recent, targeted |
| 6 | No trailing whitespace on blank lines (three copies) | generalise | One copy; emphasis removed |
| 7 | Be concise and direct | keep | Style may be switched; one line |
| 8 | No sycophancy (two copies) | generalise | One copy |
| 9 | Pragmatic engineer, push back, call out bad ideas, raise odd things | generalise | Four bullets merged into one |
| 10 | Ask early; AskUserQuestion block | generalise | "Questionnaire tool (in Claude Code, `AskUserQuestion`)"; ToolSearch loading detail dropped as Claude-only mechanics |
| 11 | Clean modular code, KISS, UNIX, functional, break tasks up | generalise | Merged into one line |
| 12 | Never duplicate code | generalise | One line, emphasis removed |
| 13 | Short feedback loops, make debugging easy | drop | Current models' default; no observed failure behind it |
| 14 | Run code after changes; never assume fixed untested | generalise | Merged into one line |
| 15 | Comments explain why (two bullets) | generalise | One line |
| 16 | Remove unneeded code only if related | keep | Scope discipline |
| 17 | Iterate on one-off scripts to learn schemas | drop | Current models do this unprompted |
| 18 | Respect `.editorconfig`, offer to add one | keep | Condensed |
| 19 | Temporary files in repo `tmp/` | keep | Conflicts with Claude Code's scratchpad default; user decision |
| 20 | User reads only end-of-turn messages | keep | Condensed |
| 21 | `gh` with `tee`; no Playwright tools | generalise | "Browser automation" instead of Playwright tool names |
| 22 | slow-command-running skill; avoid `head` | generalise | Merged into one bullet |
| 23 | `git diff --no-ext-diff` after the subcommand | keep | Harmless for others |
| 24 | `HEAD^!` meaning | drop | Current models know git revision syntax |
| 25 | Watch CI after pushing | keep | Condensed |
| new | End every final message with proposed next steps | add | Bead `ai-vtq`; previously only in the third-party style |

Nothing is left as Claude-only. `.claude/CLAUDE.md` becomes an import of
the shared file.
