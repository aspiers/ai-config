"""Shared helpers for scripts that drive Orca through its CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


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
