# Test Suite

This directory contains test suites for the AI configuration scripts and
deployment contracts.

## Git Worktree Guard Tests

`test_ai_guard_git_worktree_add.py` checks that the
`ai-guard-git-worktree-add` PreToolUse hook denies raw `git worktree add` in
the shapes agents write it (chained, with git options, after wrappers), and
allows mentions inside arguments, other `git worktree` subcommands, and the
`AI_ALLOW_GIT_WORKTREE_ADD=1` override.

```bash
python3 tests/test_ai_guard_git_worktree_add.py
```

## Stale Bug Report Guard Tests

`test_ai_guard_stale_bug_report.py` builds throwaway git repositories and
checks that the `ai-guard-stale-bug-report` PreToolUse hook denies
`bd create --type=bug` only while `HEAD` lacks commits from a local or origin
trunk, and allows other `bd` commands, other issue types, checkouts outside
git, and the `AI_ALLOW_STALE_BUG_REPORT=1` override.

```bash
python3 tests/test_ai_guard_stale_bug_report.py
```

## Unread Orca Mail Guard Tests

`test_ai_guard_orca_unread_mail.py` runs the `ai-guard-orca-unread-mail`
Stop hook against a fake Orca CLI. It checks that unread mail blocks a stop
once per message without marking it read, and that an empty mailbox, a
continued stop, a CLI failure or a terminal outside Orca all allow it.
`pi/unread-orca-mail.test.ts` and `opencode/unread-orca-mail.test.js` check
that the Pi and OpenCode adapters start a new turn only when the guard
reports mail.

```bash
python3 tests/test_ai_guard_orca_unread_mail.py
node --test --experimental-strip-types tests/pi/unread-orca-mail.test.ts
bun test tests/opencode/unread-orca-mail.test.js
```

## Orca Attention-Agent Cycling Tests

`test_orca_cycle_attention_agent.py` verifies that
`orca-cycle-attention-agent` orders blocked and waiting agents before recent
completions, drops stale or interrupted completions, joins agent panes to live
terminal handles, finds the focused pane through nested layouts, and issues
the expected `orca` CLI calls.

```bash
python3 tests/test_orca_cycle_attention_agent.py
```

## Pi Orca Tab Title Tests

`pi/pi-orca-tab-title.test.ts` verifies that the `pi-orca-tab-title` Pi
extension pins the generated short title, lets a later `/name` win, falls back
to the session name, and leaves tabs alone inside Herdr or tmux.

```bash
node --test --experimental-strip-types tests/pi/pi-orca-tab-title.test.ts
```

## Orca Extract Tests

`test_orca_extract.py` pins token and whole-line extraction, the picker
loop's copy, insert, toggle and cancel handling, which terminal is targeted,
clipboard tool selection, and the exact `orca` CLI calls made by
`orca-extract`.

```bash
python3 tests/test_orca_extract.py
```

## Orca Attention-Cycling Plugin Tests

`test_orca_attention_plugin.py` checks the `attention-cycling` plugin manifest
against the rules Orca enforces and runs its worker entry under Node to pin
the registered commands, the `~/bin` fallback, and error reporting. Requires
`node` on `PATH`.

```bash
python3 tests/test_orca_attention_plugin.py
```

## Upstreaming Status Skill Tests

`test_upstreaming_status_skill.py` verifies the skill's routing metadata,
progress-ordered `wt list`-style terminal contract, sentence-length HTML
rendering and escaping, stacked-branch dependencies, the separate Git Machete
graph, mixdown distinction, and related workflow links.

```bash
python3 tests/test_upstreaming_status_skill.py
```

## Web-Form Paste Sequence Tests

`test_submitting_upstream_paste_fields.py` runs the `submitting-upstream`
skill's `paste-form-fields.sh` against stubbed clipboard, notification and
`sleep` commands. It pins field order and labels, `#NOTE` hints, default and
overridden delays, clipboard content without a trailing newline, and the
abort on a clipboard read-back mismatch.

```bash
python3 tests/test_submitting_upstream_paste_fields.py
```

## Research Report Location Tests

`test_research_report_locations.py` verifies that cross-agent policy and the
shared reporting skills default durable reports to `docs/research/`, while
allowing explicitly configured exceptions.

```bash
python3 tests/test_research_report_locations.py
```

## FOSS Comparison Reporting Tests

`test_foss_comparison_reporting.py` verifies that FOSS research keeps its
specialist evidence checks and delegates presentation to `matrix-comparison`.
`test_matrix_comparison.py` exercises the shared renderer with non-product
alternatives, facets, missing evidence, invalid filter values and hostile text.

```bash
python3 tests/test_foss_comparison_reporting.py
python3 tests/test_matrix_comparison.py
```

## Background Human-Attention Tests

`test_background_human_attention.py` verifies that the `/bg`, `/bgp`, and
`/bed` wrappers delegate to `beads-grinding` and `beads-parallel-grinding`,
and that those skills and `beads-best-practices` keep human-needed beads out
of automatic queues, split a person's part into its own `human` bead, and
surface `bd human list` at unattended handoff.

```bash
python3 tests/test_background_human_attention.py
```

## Agent Command Parity Tests

`test_agent_command_parity.py` verifies that Codex exposes every Pi prompt
through a relative symlink, and that the shared templates have valid
frontmatter without platform-specific tool names or shell expansion.

```bash
python3 tests/test_agent_command_parity.py
```

## Global Rules Parity Tests

`test_global_rules_parity.py` verifies that Claude Code, Pi, OpenCode, and
Codex are each wired to load `.agents/AGENTS.md`, and that the file stays
small and free of trailing whitespace.

```bash
python3 tests/test_global_rules_parity.py
```

## Beads Blocker-Review Tests

`test_beads_blocker_review.py` verifies that `/blockers` separates actionable
human decisions from decisions still waiting on agent prerequisites, and that
a fresh queue read releases a decision after its final prerequisite closes.

```bash
python3 tests/test_beads_blocker_review.py
```

## AI Cockpit Contract Tests

`test_ai_cockpit_contract.py` validates the target-neutral orchestrator contract,
placeholder-only environment inventory, required security prohibitions, stable
volume names, and absence of common instance-specific identifiers.

```bash
python3 tests/test_ai_cockpit_contract.py
```

## ai-safe-rm Tests

`test_ai_safe_rm.py` - Comprehensive test suite for the `ai-safe-rm`
script.

### Running the tests

```bash
# Run all tests
python3 tests/test_ai_safe_rm.py

# Run with verbose output
python3 tests/test_ai_safe_rm.py -v

# Run specific test
python3 tests/test_ai_safe_rm.py TestAiSafeRm.test_modified_tracked_file_backed_up
```

### Test coverage

The test suite covers:

- **Unmodified tracked files** - Should be deleted directly
- **Modified tracked files** - Should be backed up to `.safe-rm/`
- **Untracked files** - Should be backed up to `.safe-rm/`
- **Multiple files** - Mixed statuses handled correctly
- **Subdirectories** - Path preservation in backups
- **Directory deletion** - Requires `-r` flag
- **Directory optimization** - All unmodified tracked uses `rm -rf`
- **Directory recursion** - Selective backup when mixed content
- **Nested structures** - Deep directory hierarchies
- **Hash collisions** - Multiple versions with same filename
- **Empty directory cleanup** - Removes empty dirs after processing
- **Error handling** - Non-existent files, not in git repo

All tests run in isolated temporary git repositories and clean up
after themselves.
