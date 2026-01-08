# AI configuration files and utilities

Adam's collection of configuration files and command-line utilities designed
to streamline common development tasks and improve productivity when working
with AI tools and configurations.

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
  - `code-linter` - Automated linting
  - `code-reviewer` - Code review analysis
  - `git-committer` - Commit message generation
  - `git-stager` - Selective git staging
  - `task-implementer` - Task implementation
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

### Scripts (`bin/`)

- **`ai-safe-rm`** - Git-aware safe file deletion script (used by safe-rm skill):
  - Tracked+unmodified files: deleted directly (recoverable from git)
  - Tracked+modified files: backed up to `.safe-rm/` with content hash
  - Untracked files: backed up to `.safe-rm/` with content hash
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
