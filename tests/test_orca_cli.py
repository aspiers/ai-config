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


class FocusedTerminalHandlesTests(unittest.TestCase):
    def test_returns_the_active_worktrees_focused_live_terminals(self) -> None:
        ps = {
            "worktrees": [
                {"worktreeId": "wt1", "isActive": True},
                {"worktreeId": "wt2"},
            ]
        }

        def leaf(tab: str, leaf_id: str) -> dict:
            return {
                "activeTabId": tab,
                "tabs": [{"tabId": tab, "activeLeafId": leaf_id}],
            }

        listing = {
            "terminals": [
                {"handle": "term_b", "tabId": "t2", "leafId": "l2"},
                {"handle": "term_a", "tabId": "t1", "leafId": "l1"},
                {"handle": "term_c", "tabId": "t3", "leafId": "l3"},
            ],
            "visualLayouts": [
                {
                    "worktreeId": "wt1",
                    "root": {
                        "type": "split",
                        "first": leaf("t1", "l1"),
                        "second": leaf("t2", "l2"),
                    },
                },
                {"worktreeId": "wt2", "root": leaf("t3", "l3")},
            ],
        }
        with patch.object(orca_cli, "run_orca", side_effect=(ps, listing)) as run:
            self.assertEqual(orca_cli.focused_terminal_handles(), ["term_a", "term_b"])

        self.assertEqual(
            [c.args[0][:2] for c in run.call_args_list],
            [["worktree", "ps"], ["terminal", "list"]],
        )


class TerminalLabelsTests(unittest.TestCase):
    def test_labels_name_the_worktree_and_strip_status_glyphs(self) -> None:
        listing = {
            "terminals": [
                {"handle": "term_a", "worktreePath": "/w/proj", "title": "⠋ Fix bug"},
                {"handle": "term_b", "worktreePath": "", "worktreeId": "floating", "title": ""},
            ]
        }
        with patch.object(orca_cli, "run_orca", return_value=listing):
            self.assertEqual(
                orca_cli.terminal_labels(["term_a", "term_b", "term_gone"]),
                {"term_a": "proj: Fix bug", "term_b": "floating", "term_gone": "?"},
            )


if __name__ == "__main__":
    unittest.main()
