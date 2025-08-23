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

- `CLAUDE.md` - Global project-specific instructions and coding rules
- `commands/` - Custom slash commands for Claude Code including commit
  helpers, task generators, and workflow automation
- `agents/` - Custom agent definitions for specialized tasks (code review,
  testing, git operations, etc.)

#### `.config/`

Application configuration files:

- `opencode/` - OpenCode AI editor configuration with custom commands,
  agents, plugins, and local LM Studio provider setup

### Scripts (`bin/`)

- **`ccu`** - Runs the latest version of `ccusage` to monitor Claude Code usage statistics
- **`ccul`** - Live monitoring of Claude Code usage with automatic refresh
  every 5 seconds using blocks display format; although for *live* monitoring,
  I actually prefer [Claude Code Usage
  Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) (`uv
  tool install claude-monitor`) (not to be confused with `npx ccmonitor` from
  [shinagaki/ccmonitor](https://github.shinagaki/ccmonitor) which also looks
  OK but far less popular)
- **`cl`** and **`claude`** - Wrappers for running the local Claude Code installation at `/home/adam/.claude/local/claude`

### `.shared_rc.d/`

Shared shell configuration fragments for common environment setup.
These are loaded by <https://github.com/aspiers/shell-env/blob/master/.shared_rc>.

## Requirements

- Bash shell
- Node.js/npm (for ccusage functionality)
- GNU Stow (for deployment)

## License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details.

## Author

Adam Spiers
