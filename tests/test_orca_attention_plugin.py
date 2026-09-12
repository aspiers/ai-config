#!/usr/bin/env python3
"""
Test suite for the attention-cycling Orca plugin.

Checks the manifest against the rules Orca enforces that matter here (worker
commands need a `main` entry, every keybinding names a contributed command
with a matching context) and drives the worker entry under Node to pin which
commands it registers and how it invokes orca-cycle-attention-agent.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).parents[1] / "orca-plugins" / "attention-cycling"
MANIFEST = json.loads((PLUGIN_DIR / "orca-plugin.json").read_text())

NODE_HARNESS = """
const m = await import(process.argv[1]);
const registered = [];
m.default({ commands: { register: (id, handler) => registered.push(id) } });
const calls = [];
const fakeRun = async (file, args) => {
  calls.push([file, args]);
  if (calls.length === 1 && process.argv[2] === 'enoent') {
    throw Object.assign(new Error('spawn ENOENT'), { code: 'ENOENT' });
  }
  if (process.argv[2] === 'fail') {
    throw Object.assign(new Error('exit 1'), { code: 1, stderr: 'no orca runtime' });
  }
  return '';
};
let failure = null;
try {
  await m.cycle('next', fakeRun, { HOME: '/home/tester' });
} catch (error) {
  failure = error.message;
}
console.log(JSON.stringify({ registered, calls, failure }));
"""


def run_harness(mode: str = "ok") -> dict:
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", NODE_HARNESS, str(PLUGIN_DIR / "main.mjs"), mode],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


class ManifestTests(unittest.TestCase):
    def test_worker_commands_have_a_main_entry_that_exists(self) -> None:
        worker_commands = [
            c for c in MANIFEST["contributes"]["commands"] if "action" not in c
        ]
        self.assertTrue(worker_commands)
        self.assertTrue((PLUGIN_DIR / MANIFEST["main"]).is_file())

    def test_keybindings_reference_commands_with_matching_context(self) -> None:
        commands = {c["id"]: c for c in MANIFEST["contributes"]["commands"]}
        for binding in MANIFEST["contributes"]["keybindings"]:
            command = commands[binding["command"]]
            self.assertEqual(binding.get("when"), command.get("context", "global"))

    def test_declares_no_capabilities(self) -> None:
        self.assertEqual(MANIFEST["capabilities"], [])


class WorkerEntryTests(unittest.TestCase):
    def test_registers_both_commands_and_runs_the_script(self) -> None:
        result = run_harness()

        self.assertEqual(
            sorted(result["registered"]),
            ["next-attention-agent", "previous-attention-agent"],
        )
        self.assertEqual(result["calls"], [["orca-cycle-attention-agent", ["next"]]])
        self.assertIsNone(result["failure"])

    def test_falls_back_to_home_bin_when_not_on_path(self) -> None:
        result = run_harness("enoent")

        self.assertEqual(
            result["calls"],
            [
                ["orca-cycle-attention-agent", ["next"]],
                ["/home/tester/bin/orca-cycle-attention-agent", ["next"]],
            ],
        )

    def test_surfaces_script_stderr_on_failure(self) -> None:
        result = run_harness("fail")

        self.assertIn("no orca runtime", result["failure"])
        self.assertEqual(len(result["calls"]), 1)


if __name__ == "__main__":
    unittest.main()
