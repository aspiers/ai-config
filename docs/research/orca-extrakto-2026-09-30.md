# Extrakto-style token extraction in Orca

Researched 2026-09-30 against Orca 1.4.205 and `stablyai/orca` `main`.

## Goal

Reproduce tmux extrakto (and the Herdr `copy-search` plugin's `extract`
mode, bound to `Ctrl+Alt+O`): grab tokens such as paths, URLs, hashes and
words from a pane's scrollback, fuzzy-pick one, then copy or insert it.

## Orca plugin API v0 cannot do it on its own

No official plugin docs exist, so this comes from source:
`src/shared/plugins/plugin-capabilities.ts` and
`src/shared/plugins/plugin-host-api.ts`.

- Capabilities are a closed set: `workspace:read`, `terminal:send`,
  `notifications:show`, `storage`, `secrets`, `events:subscribe`,
  `settings:own`.
- There is **no terminal read** method, **no clipboard** method, and **no
  "focused terminal"**. `terminal.sendText` deliberately requires an
  explicit terminal ID.
- `workspace.readContext` returns the focused worktree's branch, name and
  terminal IDs, but not which terminal is focused. Whether those IDs equal
  CLI handles (`term_…`) is unverified.
- UI contributions are commands, keybindings and sandboxed right-sidebar
  panels. There is no overlay or popup surface like Herdr's
  `placement = "overlay"`.
- Plugin keybindings never fire while a terminal has focus
  ([#15642](https://github.com/stablyai/orca/issues/15642), fix in open
  PR [#15725](https://github.com/stablyai/orca/pull/15725)). That is
  exactly when extrakto is wanted.

Escape hatch: the worker is a forked plain-Node process that can spawn
anything on `PATH`, including the `orca` CLI. The `attention-cycling`
plugin in this repo already uses that pattern.

## The `orca` CLI supplies the missing pieces

- `orca terminal read --terminal H --limit N` reads accumulated scrollback
  with escapes stripped. `--screen` reads the rendered frame instead.
  Stream mode stacks repainted lines as fragments, so TUI agent panes
  extract less cleanly than shell panes.
- `orca terminal split --terminal H --command CMD` opens a pane next to
  `H` running `CMD`. This is the nearest thing to Herdr's overlay pane.
- `orca terminal send --terminal H --text T` inserts text.
- Orca terminals support OSC 52 clipboard writes
  (`src/renderer/src/components/terminal-pane/osc52-clipboard.ts`), so a
  picker running in an Orca pane can copy.

## The extraction UI already exists

`herdr-copy-search` accepts `--input FILE` or piped stdin in place of a
Herdr pane read (`src/main.rs`), reads keys from `/dev/tty` and copies via
OSC 52. Its `--mode extract` UI can therefore run unchanged in an Orca
split. Upstream `extrakto.py` also reads stdin and could feed `fzf`
instead.

## The hard problem: which terminal?

Every process inside an Orca terminal gets `ORCA_TERMINAL_HANDLE`, so
anything triggered *from within* the pane knows its own handle.

From outside the pane (a plugin worker, keyd, a desktop hotkey), nothing
names the focused terminal directly, but it can be approximated:

- `orca terminal list --json` has no focused or active field.
- `orca worktree ps` marks the active worktree (`isActive`), and
  `orca terminal list --include-visual-layouts` gives each tab group's
  active tab and leaf. `bin/orca-cycle-attention-agent` already joins these
  in `focused_pane_keys()`. It is exact with one tab group, but when a
  worktree is split into several groups the layout does not say which group
  has focus, so it yields several candidates.
- Omitting `--terminal` resolves the "active terminal" from the caller's
  working directory, not UI focus. From `/tmp` it picked the global
  floating terminal. From this repo's worktree it picked a different pane
  from the one running the test. Treat it as unreliable.
- Issue [#19020](https://github.com/stablyai/orca/issues/19020) proposes
  `ui.readFocus` and `focusedSurface` on `readContext` for plugins. Open,
  not merged.

## Viable routes

1. **Shell panes, works today.** A zsh ZLE widget reads
   `$ORCA_TERMINAL_HANDLE`, dumps `orca terminal read` output to a temp
   file, and runs the extractor inline, inserting the pick into the
   command line. It does not help inside agent TUIs, because the shell is
   not reading keys there.
2. **Any pane, via a plugin, blocked upstream.** A plugin command with a
   keybinding spawns an `orca-extract` script. This needs #15725 so the key
   fires with a terminal focused. The worker can approximate the focused
   terminal from the visual layouts today; #19020 (or equivalent) would make
   it exact with several tab groups.
3. **Stopgap:** run tmux inside Orca terminals and keep using the real
   extrakto. It works fully, but adds a second multiplexer layer.

## Verified during implementation

- `orca terminal split --command` types the command into the split's
  interactive shell, which stays open after the command exits. Prefixing
  `exec` makes the split close about two seconds after the command exits.
- For a Claude Code pane, a stream read returns `source: screen` with only
  the visible rows (41 here), so agent TUI panes expose no scrollback.
- `herdr-copy-search` insert mode needs a Herdr source pane; with `--input`
  only copy works.

## Unverified

- Whether `workspace.readContext` terminal IDs match CLI handles.
