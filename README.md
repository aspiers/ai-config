# AI configuration files and utilities

Adam's collection of configuration files and command-line utilities designed
to streamline common development tasks and improve productivity when working
with AI tools and configurations.

## Research reports

- [FOSS managers for many active, interdependent Git
  branches](docs/research/foss-comparison-active-git-branch-managers-2026-08-25-135148Z.html) —
  the focused 11-project comparison of topology, fleet-wide restacking,
  landing, pruning, conflict recovery, worktree behavior and automation.
- [FOSS branch, worktree, and integration-mix tools for an AI development
  cockpit](docs/research/foss-comparison-git-branch-worktree-cockpit-2026-08-25-133027Z.html) —
  the expanded 12-project comparison, including git-stint, the capability-layer map, and
  recommendations for composing Worktrunk, branch topology, AgentBox, Herdr,
  T3 Code, and a disposable fan-in target.
- [Parallel Git branch and worktree management
  comparison](docs/foss-git-branch-worktree-management-comparison-2026-08-11.html) —
  the earlier six-project comparison retained as the original research
  snapshot.

## Installation

This configuration is designed to be installed using [GNU
Stow](https://www.gnu.org/software/stow/) to create symlinks from within your
home directory:

```bash
git clone https://github.com/adamspiers/ai-config.git
stow -d . -t ~ ai-config
```

To remove:

```bash
stow -d . -t ~ -D ai-config
```

Alternatively, you can manually copy individual files to your desired
locations. This project is licensed under the GPL v3, so please preserve the
license information when redistributing or modifying the code.

## Contents

### AI agent configuration

#### `.claude/`

Claude Code configuration containing:

- `CLAUDE.md` - Global instructions and coding rules
- `settings.json` - Permission configuration for allowed bash commands
- `commands/` - Custom slash commands:
  - `commit` - Intelligent git commit workflow
  - `do` - Task execution helper
  - `dry` - Dry-run mode for testing changes
  - `gen-prp` - Generate PR descriptions
  - `gen-tasks` - Generate task lists from specifications
  - `init2` - Project initialization
  - `iter` - Iterative development workflow
  - `lint` - Code linting
  - `obs` - Obsidian integration
  - `reflect` - Self-reflection prompt
  - `review` - Code review
  - `small` - Small change workflow
  - `stage` - Git staging helper
  - `test` - Test runner
- `agents/` - Specialized sub-agents:
  - `code-deduplicator` - Remove code duplication
  - `code-linter` - Automated linting
  - `code-refactorer` - Refactor large code units
  - `code-reviewer` - Code review analysis
  - `doc-updater` - Update documentation based on learnings
  - `git-committer` - Commit message generation
  - `git-stager` - Selective git staging
  - `prp-generator` - Generate Product Requirements Prompts
  - `task-generator` - Generate tasks from PRPs
  - `task-implementer` - Task implementation
  - `task-orchestrator` - Complete workflow orchestration
  - `test-runner` - Test execution
- `skills/` - [Agent Skills](https://agentskills.io/) (modular capability packages):
  - `safe-rm/` - Safe file deletion with git-aware backup
  - `git-staging/` - Non-interactive git staging techniques

#### `.config/opencode/`

[OpenCode](https://opencode.ai/) configuration (parallel to Claude Code):

- `opencode.json` - Main configuration with permission settings
- `opencode-lmstudio.json` - Local LM Studio provider setup
- `command/` - Slash commands (mirrors `.claude/commands/`)
- `agent/` - Sub-agents (mirrors `.claude/agents/`, plus `task-orchestrator`)
- `plugin/` - JavaScript plugins:
  - `env-protection.js` - Prevents exposure of environment variables
  - `notification.js` - Desktop notifications for agent events

#### `.pi/agent/`

[Pi](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent)
configuration containing:

- `settings.json` - Provider, model, package, status-line, tool-rendering, and
  extension settings
- `keybindings.json` - Emacs-style editor bindings and local key overrides
- `prompts/` - Slash-command prompt templates, mostly thin wrappers which
  delegate to the shared skills under `.agents/skills/`
- `extensions/desktop-theme-sync.ts` - Watches `$XDG_CONFIG_HOME/theme` and
  maps its `light` or `dark` value to the themes configured in
  `theme-sync.json`; `/theme-sync` reports the current synchronization state
- `extensions/herdr-agent-state.ts` - Herdr-managed integration which reports
  Pi sessions as working, idle, or blocked; reinstalling Herdr may overwrite
  it
- `extensions/quotas.json` and `extensions/powerline-footer/theme.json` -
  Quota display and powerline presentation settings
- `pi-resource-center-settings.json` - Resource-center display and external
  skill-source settings

Skills are not maintained directly under `.pi/agent/`. The shared,
cross-platform skill sources live under `.agents/skills/` and Pi discovers
them through its configured packages and importers.

##### Local-only state

Authentication data, sessions, downloaded Git packages, caches, and extension
logs are intentionally excluded by `.gitignore`. They must not be added to
this public repository.

##### Author-specific integrations and package sources

> **⚠️ AUTHOR-SPECIFIC:** The following choices support the author's desktop
> and Herdr setup. Other users should substitute their own integrations and
> normally use published package releases.

- `git:github.com/justcyl/pi-herdr-tab-sync` installs the Herdr tab and agent
  state integration used by `extensions/herdr-agent-state.ts`.
- `pi-ask-user` is temporarily installed from the author's
  [fix/number-custom-response branch](https://github.com/aspiers/pi-ask-user/tree/fix/number-custom-response)
  instead of npm. The branch numbers the custom-response option and lets its
  number key open the freeform editor without changing canned-answer number-key
  behavior. Once that enhancement is released upstream, replace the Git branch
  pin with `npm:pi-ask-user`.
- `pi-status` is installed from the author's
  [fix/pi-status-title-renames branch](https://github.com/aspiers/pi-status/tree/fix/pi-status-title-renames),
  which reapplies the configured title after Pi's `/name` command or
  `pi-tmux-window-name`'s asynchronous `/rename` command changes it.

#### `.codex/`

[Codex](https://developers.openai.com/codex/) configuration containing:

- `config.toml` - Model, reasoning effort, approvals, feature flags, hook
  trust state, and MCP server definitions
- `hooks.json` - Session and tool-use hooks
- `prompts/` - Custom slash commands, as prompt templates that invoke skills
  directly. Codex has no subagents, so these mirror the Pi templates in
  `.pi/agent/prompts/` rather than the Claude Code and OpenCode commands.

Codex reads `AGENTS.md` automatically, so the repository's instructions apply
without further configuration.

#### `.orca/`

Orca configuration containing:

- `keybindings.json` - Per-platform keyboard shortcut overrides

Only this file is tracked. Orca's other state under `~/.orca/` is
deliberately left unmanaged and is excluded by `.gitignore`:

- `agent-hooks/` - Orca's own hook shims, referenced by absolute path from
  the hook blocks Orca injects into `.claude/settings.json` and
  `.codex/hooks.json`. They are an implementation detail of the app rather
  than settings authored here
- `linear-workspaces.json` and `linear-tokens/` - Linear account identifiers
  and an encrypted credential, which must never enter a public repository

Orca's other location, `~/.config/orca/`, is an Electron application profile
directory rather than a settings directory, and none of it is tracked or
stowed. It holds live secrets (a runtime auth token, a mobile device pairing
token, an E2EE keypair, a session authority key), account identity, rolling
usage and session data, and browser caches. The known paths are named
explicitly in `.gitignore` so that a stray `git add -A` cannot commit a
credential to this public repository's permanent history.

#### Response output styles

The agents here share a single response style, sourced from
[attention-span](https://github.com/alexgreensh/attention-span) (answer-first,
plain English, built for skimming).

attention-span is AGPL-3.0, so its text is **not** vendored into this public
repository. `bin/attention-span-install` wires a local clone into each agent
instead, using whichever mechanism that agent actually supports:

| Agent | Mechanism | Path |
| ----- | --------- | ---- |
| Claude Code | native output styles | `~/.claude/output-styles/` |
| Pi | appended system prompt | `~/.pi/agent/APPEND_SYSTEM.md` |
| OpenCode | global instructions | `~/.config/opencode/AGENTS.md` |
| Codex | global instructions | `~/.codex/AGENTS.md` |

Only Claude Code has a real output-style feature, including a `/style` picker
for switching between the bundled styles. Installing the files does not
activate one: this repository's global Claude Code settings select
`Attention-kind` through `outputStyle`. For the other agents the style is a
system-prompt fragment applied at startup, so switching means re-running the
installer with `ATTENTION_SPAN_STYLE` set and restarting the agent.

For OpenCode and Codex the style is the *weakest* layer: it is merged ahead of
this repository's own `AGENTS.md`, so project instructions win on conflict.

> **Codex budget:** Codex reads at most `project_doc_max_bytes` (32 KiB by
> default) across all `AGENTS.md` files combined, skipping the remainder once
> that is exhausted. The style file plus this repository's `AGENTS.md` come to
> roughly 24 KiB, so keep an eye on the headroom before adding much more.

The installer strips the Claude-Code-specific YAML frontmatter for the other
agents, since feeding them a `name:`/`keep-coding-instructions:` block would
only waste tokens describing a key they cannot use.

```bash
git clone https://github.com/alexgreensh/attention-span \
    ~/.GIT/3rd-party/attention-span
bin/attention-span-install                        # default: attention-kind
ATTENTION_SPAN_STYLE=spartan bin/attention-span-install
```

Re-run it after updating the clone to refresh the generated prompt bodies.

#### Command and Agent Delegation

Commands (`.claude/commands/` and `.config/opencode/command/`) and agents
(`.claude/agents/` and `.config/opencode/agents/`) are designed as thin wrappers
that delegate to skills. This ensures:

- No duplication of implementation content between platforms
- Single source of truth in skills (`.agents/skills/`)
- Easy maintenance and consistency

See [AGENTS.md](AGENTS.md) for the detailed delegation pattern.

### Scripts (`bin/`)

- **`ai-safe-rm`** - Git-aware safe file deletion script (used by safe-rm skill):
  - Tracked+unmodified files: deleted directly (recoverable from git)
  - Tracked+modified files: backed up to `.safe-rm/` with content hash
  - Untracked files: backed up to `.safe-rm/` with content hash
- **`attention-span-install`** - Deploys the shared response output style to
  Claude Code, Pi, OpenCode, and Codex from a local attention-span clone. See
  "Response output styles" above.
- **`audit-npm-packages`** - Downloads npm tarballs with `npm pack --ignore-scripts`
  and emits a JSON security-audit summary covering npm metadata, lifecycle
  scripts, Pi extension metadata, dependency names, and simple risky source
  pattern counts:
  - Example: `audit-npm-packages --output /tmp/audit.json pi-web-access pi-lens`
- **`ccu`** - Runs the latest version of `ccusage` to monitor Claude Code usage statistics
- **`ccul`** - Live monitoring of Claude Code usage with automatic refresh
  every 5 seconds using blocks display format; although for *live* monitoring,
  I actually prefer [Claude Code Usage
  Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) (`uv
  tool install claude-monitor`) (not to be confused with `npx ccmonitor` from
  [shinagaki/ccmonitor](https://github.shinagaki/ccmonitor) which also looks
  OK but far less popular)
- **`cl`** and **`claude`** - Wrappers for running the local Claude Code installation
- **`cursor`** - Launches Cursor IDE with systemd resource limits (memory, CPU, I/O)
- **`orca-cycle-attention-agent`** - Focuses the previous or next Orca agent
  that needs attention (blocked or waiting for input first, then recently
  finished, newest first), via the `orca` CLI. Orca has no built-in shortcut
  for this
  ([stablyai/orca#12577](https://github.com/stablyai/orca/issues/12577)), so
  the `orca-plugins/attention-cycling` plugin binds it inside Orca. Finds
  Orca's CLI via its Linux shim or `orca-ide` rather than bare `orca`, which
  on Linux is the GNOME screen reader; set `ORCA_CLI` to override
- **`llm-setup`** - Installs/upgrades [llm](https://llm.datasette.io/) with common plugins
  (gpt4all, anthropic, gemini, openrouter, deepseek)

### Orca plugins (`orca-plugins/`)

Plugins for [Orca](https://github.com/stablyai/orca), loaded as development
plugins rather than stowed: Orca rejects symlinks inside plugin content, so
point it at this checkout's real path.

- **`attention-cycling`** - Binds `Alt+Shift+Up` / `Alt+Shift+Down` inside
  Orca to `orca-cycle-attention-agent previous` / `next`. Orca's own
  keybindings cannot run shell commands, but a plugin's worker-backed
  commands can, so this is the only way to get an in-app shortcut without
  a global hotkey. To enable it, open Orca's Settings, Plugins, add this
  plugin's directory as a development plugin path, and approve it. The
  worker only inherits `PATH` and `HOME`, so the script must be on `PATH`
  or in `~/bin`.

### AppArmor profiles (`root-etc-stow-pkg/apparmor.d/`)

WIP security profiles for sandboxing AI agents:

- `abstractions/ai-agent-base` - Base permissions (network, temp dirs, sensitive file deny rules)
- `abstractions/ai-agent-git` - Git operations
- `abstractions/ai-agent-github` - GitHub CLI access
- `abstractions/ai-agent-npm` - npm/Node.js operations
- `abstractions/ai-agent-opencode` - OpenCode-specific permissions
- `abstractions/ai-agent-safe-commands` - Whitelisted safe commands
- `home.adam.bin.oc` - Main OpenCode profile

### Shell configuration (`.shared_rc.d/`)

Shell configuration fragments loaded by
[shell-env](https://github.com/aspiers/shell-env):

- `lmstudio` - Adds LM Studio bin directory to PATH

### Testing (`tests/`)

- `test_ai_safe_rm.py` - Unit tests for the `ai-safe-rm` script
- `test_orca_cycle_attention_agent.py` - Unit tests for the
  `orca-cycle-attention-agent` script
- `test_orca_attention_plugin.py` - Tests for the `attention-cycling` Orca
  plugin manifest and worker entry

### Other files

- `AGENTS.md` - Instructions for AI agents working in this repository
- `.editorconfig` - Editor formatting rules
- `.stow-local-ignore` - Files to exclude from stow deployment

## Requirements

- Bash shell
- Node.js/npm (for ccusage functionality)
- GNU Stow (for deployment)

## License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details.

## Author

Adam Spiers
