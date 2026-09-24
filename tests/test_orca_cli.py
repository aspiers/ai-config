#!/usr/bin/env python3
"""
Test suite for bin/orca_cli.py, the Orca CLI helpers shared by the orca-*
scripts: which binary gets run, and how JSON envelopes are unwrapped.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "bin"))

import orca_cli  # noqa: E402


class OrcaCliResolutionTests(unittest.TestCase):
    def test_env_override_wins(self) -> None:
        self.assertEqual(orca_cli.orca_cli({"ORCA_CLI": "/opt/orca"}), "/opt/orca")

    def test_prefers_the_linux_shim_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as config_home:
            shim_dir = Path(config_home) / "orca" / "linux-orca-cli-shim"
            shim_dir.mkdir(parents=True)
            (shim_dir / "orca").write_text("#!/bin/sh\n")

            self.assertEqual(
                orca_cli.orca_cli({"XDG_CONFIG_HOME": config_home}), str(shim_dir / "orca")
            )

    def test_falls_back_to_orca_ide_then_bare_orca(self) -> None:
        with tempfile.TemporaryDirectory() as bin_dir:
            cli = Path(bin_dir) / "orca-ide"
            cli.write_text("#!/bin/sh\n")
            cli.chmod(0o755)
            env = {"XDG_CONFIG_HOME": "/nonexistent", "PATH": bin_dir}

            self.assertEqual(orca_cli.orca_cli(env), str(cli))
            self.assertEqual(orca_cli.orca_cli({**env, "PATH": "/nonexistent"}), "orca")


class RunOrcaTests(unittest.TestCase):
    def test_reports_non_json_output(self) -> None:
        completed = Mock(stdout="Screen reader started\n", stderr="", returncode=0)
        with patch.object(orca_cli.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "non-JSON output"):
                orca_cli.run_orca(["worktree", "ps"])

    def test_raises_on_error_envelope(self) -> None:
        completed = Mock(
            stdout='{"ok": false, "error": {"code": "terminal_handle_stale"}}',
            stderr="",
            returncode=1,
        )
        with patch.object(orca_cli.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "terminal_handle_stale"):
                orca_cli.run_orca(["terminal", "switch", "--terminal", "x"])


if __name__ == "__main__":
    unittest.main()
