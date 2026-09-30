#!/usr/bin/env python3
"""
Test suite for the orca-extract script.

Pins the exact `orca` CLI calls, that the capture file holds the terminal's
lines and is removed when the split fails, and that the generated shell line
runs the picker on the capture, passes config through, and deletes it after.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

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

LINES = ["$ ls", "src/main.rs  https://example.com/a b"]


def read_result(lines: list[str]) -> dict:
    return {"terminal": {"tail": lines}}


class OpenPickerTests(unittest.TestCase):
    def test_reads_then_splits_beside_the_source_terminal(self) -> None:
        split = {"split": {"handle": "term_new"}}
        with patch.object(
            MODULE, "run_orca", side_effect=(read_result(LINES), split)
        ) as run_orca:
            handle = MODULE.open_picker("term_src", 500, "pick", "vertical", {})

        self.assertEqual(handle, "term_new")
        read_call, split_call = (c.args[0] for c in run_orca.call_args_list)
        self.assertEqual(
            read_call, ["terminal", "read", "--terminal", "term_src", "--limit", "500"]
        )
        self.assertEqual(
            split_call[:6],
            ["terminal", "split", "--terminal", "term_src", "--direction", "vertical"],
        )
        self.assertEqual(split_call[6], "--command")
        capture = Path(split_call[7].split("--input ")[1].split(";")[0])
        self.assertEqual(capture.read_text(encoding="utf-8"), "\n".join(LINES) + "\n")
        capture.unlink()

    def test_omits_direction_when_not_given(self) -> None:
        split = {"split": {"handle": "term_new"}}
        with patch.object(
            MODULE, "run_orca", side_effect=(read_result(LINES), split)
        ) as run_orca:
            MODULE.open_picker("term_src", 500, "pick", None, {})

        split_call = run_orca.call_args_list[1].args[0]
        self.assertNotIn("--direction", split_call)
        Path(split_call[-1].split("--input ")[1].split(";")[0]).unlink()

    def test_removes_the_capture_when_the_split_fails(self) -> None:
        created: list[Path] = []
        real_write = MODULE.write_capture

        def recording_write(lines: list[str]) -> Path:
            created.append(real_write(lines))
            return created[-1]

        with (
            patch.object(MODULE, "write_capture", side_effect=recording_write),
            patch.object(
                MODULE,
                "run_orca",
                side_effect=(read_result(LINES), RuntimeError("split failed")),
            ),
            self.assertRaises(RuntimeError),
        ):
            MODULE.open_picker("term_src", 500, "pick", None, {})

        self.assertEqual(len(created), 1)
        self.assertFalse(created[0].exists())


class PickerCommandTests(unittest.TestCase):
    def run_line(self, environment: dict[str, str]) -> tuple[str, Path]:
        """Run the generated line with a fake picker; return what it saw."""
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / "record"
            picker = Path(tmp) / "fake picker"
            picker.write_text(
                "#!/bin/sh\n"
                f'{{ printf "%s\\n" "$@"; cat "$4"; '
                f'echo "cfg=$HERDR_PLUGIN_CONFIG_DIR"; }} > "{record}"\n',
                encoding="utf-8",
            )
            picker.chmod(0o755)
            capture = MODULE.write_capture(LINES)
            line = MODULE.picker_command(str(picker), capture, environment)
            env = {
                k: v for k, v in os.environ.items() if k != "HERDR_PLUGIN_CONFIG_DIR"
            }
            # Run as an interactive shell would: the line is the whole command.
            subprocess.run(["sh", "-c", line], check=True, env=env)
            return record.read_text(encoding="utf-8"), capture

    def test_runs_picker_on_capture_then_deletes_it(self) -> None:
        seen, capture = self.run_line({})
        self.assertEqual(
            seen,
            f"--mode\nextract\n--input\n{capture}\n" + "\n".join(LINES) + "\ncfg=\n",
        )
        self.assertFalse(capture.exists())

    def test_passes_picker_config_dir_through(self) -> None:
        seen, _ = self.run_line({"HERDR_PLUGIN_CONFIG_DIR": "/cfg dir"})
        self.assertTrue(seen.endswith("cfg=/cfg dir\n"))

    def test_line_starts_with_space_and_execs(self) -> None:
        line = MODULE.picker_command("pick", Path("/tmp/x"), {})
        self.assertTrue(line.startswith(" exec sh -c "))


class MainTests(unittest.TestCase):
    def test_fails_without_a_terminal(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ORCA_TERMINAL_HANDLE"}
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("no terminal", completed.stderr)


if __name__ == "__main__":
    unittest.main()
