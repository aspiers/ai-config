#!/usr/bin/env python3
"""
Test suite for the orca-extract script.

Pins token and line extraction, the picker loop's copy, insert, toggle and
cancel handling, which terminal is targeted, and the exact `orca` CLI calls.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import Mock, patch

BIN_DIR = Path(__file__).parents[1] / "bin"
SCRIPT = BIN_DIR / "orca-extract"
# The script imports its shared orca_cli module from its own directory.
sys.path.insert(0, str(BIN_DIR))
SPEC = importlib.util.spec_from_loader(
    "orca_extract", SourceFileLoader("orca_extract", str(SCRIPT))
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

LINES = [
    "See https://github.com/o/r/issues/1, then edit ~/.config/app.conf.",
    'Run "git log --oneline" in src/main/ (commit 4930f47abc).',
    "━━━━━━━━━━ │ ❯",
]


def read_result(lines: list[str]) -> dict:
    return {"terminal": {"tail": lines}}


class ExtractionTests(unittest.TestCase):
    def test_tokens_are_newest_first_and_cover_each_kind(self) -> None:
        self.assertEqual(
            MODULE.tokens(LINES),
            [
                "git log --oneline",
                "src/main/",
                "--oneline",
                "commit",
                "4930f47abc",
                "https://github.com/o/r/issues/1",
                "~/.config/app.conf",
            ],
        )

    def test_url_paths_and_trailing_punctuation_are_not_separate_tokens(self) -> None:
        tokens = MODULE.tokens(["see https://example.com/a/b, ok"])
        self.assertIn("https://example.com/a/b", tokens)
        self.assertNotIn("/example.com/a/b", tokens)
        self.assertNotIn("https://example.com/a/b,", tokens)

    def test_tokens_deduplicate_keeping_the_newest(self) -> None:
        self.assertEqual(
            MODULE.tokens(["alpha12", "beta123", "alpha12"]),
            [
                "alpha12",
                "beta123",
            ],
        )

    def test_whole_lines_skip_borders_and_blanks(self) -> None:
        self.assertEqual(
            MODULE.whole_lines(["first line", "", "━━━ │", "  second line  "]),
            ["second line", "first line"],
        )


class ExtractLoopTests(unittest.TestCase):
    def run_extract(self, picks: list[tuple[int, str]], handles=("term_a",)):
        pick = Mock(side_effect=picks)
        copy, insert = Mock(), Mock()
        with patch.object(
            MODULE, "run_orca", return_value=read_result(LINES)
        ) as run_orca:
            outcome = MODULE.extract(list(handles), 500, "wt: tab", pick, copy, insert)
        return outcome, pick, copy, insert, run_orca

    def test_enter_copies_the_choice(self) -> None:
        outcome, pick, copy, insert, run_orca = self.run_extract([(MODULE.COPY, "x1")])
        self.assertEqual(outcome, "copied")
        copy.assert_called_once_with("x1")
        insert.assert_not_called()
        run_orca.assert_called_once_with(
            ["terminal", "read", "--terminal", "term_a", "--limit", "500"]
        )
        self.assertEqual(pick.call_args.args[1:], ("word", "wt: tab"))

    def test_tab_inserts_into_the_single_target(self) -> None:
        outcome, _, copy, insert, _ = self.run_extract([(MODULE.INSERT, "x1")])
        self.assertEqual(outcome, "inserted into term_a")
        insert.assert_called_once_with("term_a", "x1")
        copy.assert_not_called()

    def test_tab_copies_when_the_target_is_ambiguous(self) -> None:
        outcome, _, copy, insert, _ = self.run_extract(
            [(MODULE.INSERT, "x1")], handles=("term_a", "term_b")
        )
        self.assertIn("ambiguous", outcome)
        copy.assert_called_once_with("x1")
        insert.assert_not_called()

    def test_ctrl_t_toggles_to_lines_and_back(self) -> None:
        _, pick, copy, _, _ = self.run_extract(
            [(MODULE.TOGGLE, ""), (MODULE.TOGGLE, ""), (MODULE.COPY, "x1")]
        )
        modes = [c.args[1] for c in pick.call_args_list]
        self.assertEqual(modes, ["word", "line", "word"])
        self.assertEqual(pick.call_args_list[1].args[0], MODULE.whole_lines(LINES))
        copy.assert_called_once_with("x1")

    def test_escape_does_nothing(self) -> None:
        outcome, _, copy, insert, _ = self.run_extract([(MODULE.CANCEL, "")])
        self.assertEqual(outcome, "cancelled")
        copy.assert_not_called()
        insert.assert_not_called()


class RofiPickTests(unittest.TestCase):
    def run_pick(self, returncode: int, stdout: str = "", stderr: str = ""):
        completed = Mock(returncode=returncode, stdout=stdout, stderr=stderr)
        with patch.object(MODULE.subprocess, "run", return_value=completed) as run:
            return MODULE.rofi_pick(["a1", "b2"], "word", "wt: tab"), run

    def test_returns_the_exit_code_and_choice(self) -> None:
        (code, choice), run = self.run_pick(MODULE.INSERT, "b2\n")
        self.assertEqual((code, choice), (MODULE.INSERT, "b2"))
        self.assertEqual(run.call_args.kwargs["input"], "a1\nb2")
        self.assertIn("extract (word) from wt: tab", run.call_args.args[0])

    def test_uses_the_configured_rofi_wrapper_with_its_arguments(self) -> None:
        self.assertEqual(MODULE.rofi_command({}), ["rofi"])
        self.assertEqual(
            MODULE.rofi_command({"ORCA_EXTRACT_ROFI": "my-rofi -F 'x l'"}),
            ["my-rofi", "-F", "x l"],
        )

    def test_plain_escape_is_a_cancel(self) -> None:
        (code, _), _ = self.run_pick(MODULE.CANCEL)
        self.assertEqual(code, MODULE.CANCEL)

    def test_rofi_failure_is_not_mistaken_for_a_cancel(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "cannot open display"):
            self.run_pick(MODULE.CANCEL, stderr="cannot open display\n")


class InsertTests(unittest.TestCase):
    def test_types_the_text_without_pressing_enter(self) -> None:
        with patch.object(MODULE, "run_orca", return_value={}) as run_orca:
            MODULE.insert_into("term_a", "x1")
        run_orca.assert_called_once_with(
            ["terminal", "send", "--terminal", "term_a", "--text", "x1"]
        )


class TargetTests(unittest.TestCase):
    def test_explicit_terminal_wins(self) -> None:
        env = {"ORCA_TERMINAL_HANDLE": "term_own"}
        self.assertEqual(MODULE.target_handles("term_x", False, env), ["term_x"])

    def test_defaults_to_own_pane_inside_orca(self) -> None:
        env = {"ORCA_TERMINAL_HANDLE": "term_own"}
        self.assertEqual(MODULE.target_handles(None, False, env), ["term_own"])

    def test_uses_focused_terminal_outside_orca_or_when_asked(self) -> None:
        with patch.object(MODULE, "focused_terminal_handles", return_value=["term_f"]):
            self.assertEqual(MODULE.target_handles(None, False, {}), ["term_f"])
            self.assertEqual(
                MODULE.target_handles(None, True, {"ORCA_TERMINAL_HANDLE": "term_own"}),
                ["term_f"],
            )


class ClipboardTests(unittest.TestCase):
    def test_prefers_wl_copy_under_wayland_then_xclip(self) -> None:
        with patch.object(MODULE.shutil, "which", return_value="/usr/bin/x"):
            self.assertEqual(
                MODULE.clipboard_command({"WAYLAND_DISPLAY": "wayland-0"}),
                ["wl-copy"],
            )
            self.assertEqual(
                MODULE.clipboard_command({}), ["xclip", "-selection", "clipboard"]
            )

    def test_fails_clearly_without_a_clipboard_tool(self) -> None:
        with (
            patch.object(MODULE.shutil, "which", return_value=None),
            self.assertRaisesRegex(RuntimeError, "no clipboard tool"),
        ):
            MODULE.clipboard_command({})


if __name__ == "__main__":
    unittest.main()
