"""Shared helpers for scripts that drive Orca through its CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Orca pages its listings (default 200 worktrees); ask for far more than any
# real session holds so a busy host cannot hide a terminal behind the cap.
LISTING_LIMIT = "10000"


def orca_cli(environment: dict[str, str]) -> str:
    """Locate Orca's CLI rather than trusting a bare ``orca`` on PATH.

    On packaged Linux, Orca deliberately leaves ``orca`` to the GNOME screen
    reader and only puts its shim on PATH inside terminals it spawns, so a
    hotkey or plugin worker that inherits the app's PATH would otherwise run
    the wrong program (stablyai/orca#7904).
    """
    override = environment.get("ORCA_CLI")
    if override:
        return override
    config_home = environment.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    shim = Path(config_home) / "orca" / "linux-orca-cli-shim" / "orca"
    if shim.is_file():
        return str(shim)
    # Packaged Linux registers the CLI globally under this name instead.
    return shutil.which("orca-ide", path=environment.get("PATH")) or "orca"


def run_orca(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [orca_cli(dict(os.environ)), *args, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if not completed.stdout.strip():
        detail = completed.stderr.strip() or f"exit status {completed.returncode}"
        raise RuntimeError(f"orca {' '.join(args)} produced no JSON: {detail}")
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"orca {' '.join(args)} returned non-JSON output; is the right "
            f"Orca CLI being run? Set ORCA_CLI to override: {error}"
        ) from error
    if not response.get("ok"):
        error = response.get("error") or {}
        raise RuntimeError(
            f"orca {' '.join(args)} failed: "
            f"{error.get('code', 'unknown')}: {error.get('message', 'no message')}"
        )
    return response["result"]


def terminal_handles(terminals: list[dict[str, Any]]) -> dict[str, str]:
    """Map each live terminal's pane key (``tabId:leafId``) to its handle."""
    return {
        f"{terminal['tabId']}:{terminal['leafId']}": terminal["handle"]
        for terminal in terminals
        if terminal.get("connected", True)
        and terminal.get("tabId")
        and terminal.get("leafId")
        and terminal.get("handle")
    }


def active_pane_keys(node: dict[str, Any]) -> set[str]:
    """Pane keys of the active leaf in every group's active tab under ``node``."""
    if node.get("type") == "split":
        return active_pane_keys(node["first"]) | active_pane_keys(node["second"])
    active_tab_id = node.get("activeTabId")
    for tab in node.get("tabs", []):
        if tab.get("tabId") == active_tab_id and tab.get("activeLeafId"):
            return {f"{active_tab_id}:{tab['activeLeafId']}"}
    return set()


def focused_pane_keys(
    worktrees: list[dict[str, Any]], layouts: list[dict[str, Any]]
) -> set[str]:
    """Pane keys that may currently hold focus.

    The layout snapshot marks the active tab per group but not the active
    group, so a worktree split into several groups yields several keys.
    """
    active_ids = {wt["worktreeId"] for wt in worktrees if wt.get("isActive")}
    keys: set[str] = set()
    for layout in layouts:
        if layout.get("worktreeId") in active_ids:
            keys |= active_pane_keys(layout.get("root", {}))
    return keys


def focused_terminal_handles() -> list[str]:
    """Handles of the terminals that may hold focus, in a stable order.

    Orca exposes no focused terminal directly, so this joins the active
    worktree with each tab group's active leaf; see focused_pane_keys for
    why more than one handle can come back.
    """
    ps = run_orca(["worktree", "ps", "--limit", LISTING_LIMIT])
    listing = run_orca(
        ["terminal", "list", "--include-visual-layouts", "--limit", LISTING_LIMIT]
    )
    handles = terminal_handles(listing.get("terminals", []))
    keys = focused_pane_keys(ps.get("worktrees", []), listing.get("visualLayouts", []))
    return sorted(handles[key] for key in keys if key in handles)


def log_line(client: str, message: str, path: Path | None) -> None:
    """Report to stderr and optionally a file, for hotkey runs whose stdio
    is discarded."""
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {client}: {message}"
    print(line, file=sys.stderr)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
