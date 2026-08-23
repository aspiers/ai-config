# AI configuration files and utilities

Adam's collection of configuration files and command-line utilities designed
to streamline common development tasks and improve productivity when working
with AI tools and configurations.

## Research reports

- [FOSS branch, worktree, and integration-mix tools for an AI development
  cockpit](docs/foss-git-branch-worktree-cockpit-comparison-2026-08-18.html) —
  the expanded 11-project comparison, including the capability-layer map and
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
- **`audit-npm-packages`** - Downloads npm tarballs with `npm pack --ignore-scripts`
  and emits a JSON security-audit summary covering npm metadata, lifecycle
  scripts, Pi extension metadata, dependency names, and simple risky source
  pattern counts:
  - Example: `audit-npm-packages --output /tmp/audit.json pi-web-access pi-lens`
- **`ccu`** - Runs the latest version of `ccusage` to monitor Claude Code usage statistics
- **`ccul`** - Live monitoring of Claude Code usage with automatic refresh
  every 5 seconds using blocks display format; although for _live_ monitoring,
  I actually prefer [Claude Code Usage
  Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) (`uv
  tool install claude-monitor`) (not to be confused with `npx ccmonitor` from
  [shinagaki/ccmonitor](https://github.shinagaki/ccmonitor) which also looks
  OK but far less popular)
- **`cl`** and **`claude`** - Wrappers for running the local Claude Code installation
- **`cursor`** - Launches Cursor IDE with systemd resource limits (memory, CPU, I/O)
- **`llm-setup`** - Installs/upgrades [llm](https://llm.datasette.io/) with common plugins
  (gpt4all, anthropic, gemini, openrouter, deepseek)

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
