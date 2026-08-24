#!/usr/bin/env python3
"""Tests for prerequisite-aware review of human-owned Beads issues."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/beads-blocker-review/SKILL.md"
HELPER = SKILL.parent / "scripts/list-actionable-human-beads.py"
CLAUDE_COMMAND = ROOT / ".claude/commands/blockers.md"


class TestBeadsBlockerReview(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.mock_bd = Path(self.temporary_directory.name) / "bd"
        self.mock_bd.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys

                if sys.argv[1:] == ["human", "list", "--json"]:
                    result = [
                        {"id": "ready-human", "title": "Ready decision"},
                        {"id": "waiting-human", "title": "Waiting decision"},
                    ]
                elif sys.argv[1:] == [
                    "ready", "--label=human", "--limit=0", "--brief", "--json"
                ]:
                    ready_ids = filter(None, os.environ.get("MOCK_READY", "").split(","))
                    result = [{"id": issue_id} for issue_id in ready_ids]
                else:
                    raise SystemExit(f"unexpected arguments: {sys.argv[1:]}")
                print(json.dumps(result))
                """
            )
        )
        self.mock_bd.chmod(0o755)

    def run_helper(self, ready_ids: str) -> dict:
        environment = os.environ.copy()
        environment["MOCK_READY"] = ready_ids
        environment["PATH"] = os.pathsep.join(
            [self.temporary_directory.name, environment["PATH"]]
        )
        result = subprocess.run(
            [str(HELPER)],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
            cwd=self.temporary_directory.name,
        )
        return json.loads(result.stdout)

    def test_partitions_ready_and_prerequisite_blocked_human_beads(self):
        result = self.run_helper("ready-human")

        self.assertEqual(result["counts"], {"actionable": 1, "waiting": 1})
        self.assertEqual(
            [issue["id"] for issue in result["actionable"]],
            ["ready-human"],
        )
        self.assertEqual(
            [issue["id"] for issue in result["waiting"]],
            ["waiting-human"],
        )

    def test_fresh_read_releases_human_bead_after_prerequisite_closes(self):
        first_result = self.run_helper("ready-human")
        second_result = self.run_helper("ready-human,waiting-human")

        self.assertEqual(first_result["counts"]["actionable"], 1)
        self.assertEqual(second_result["counts"], {"actionable": 2, "waiting": 0})
        self.assertEqual(
            [issue["id"] for issue in second_result["actionable"]],
            ["ready-human", "waiting-human"],
        )

    def test_rejects_beads_command_override(self):
        result = subprocess.run(
            [str(HELPER), "--bd-command", "/bin/true"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments: --bd-command", result.stderr)

    def test_skill_prompts_only_actionable_partition(self):
        text = SKILL.read_text()

        self.assertTrue(HELPER.is_file())
        self.assertIn("`scripts/list-actionable-human-beads.py`", text)
        self.assertIn("relative to this `SKILL.md`", text)
        self.assertIn("Never prompt an item from `waiting`", text)
        self.assertRegex(
            text,
            r"Run the helper again\s+rather\s+than reusing its output",
        )
        self.assertIn('bd show "$id" --json', text)
        self.assertIn("one-bead-one-doer rule", text)

    def test_claude_command_allows_bundled_helper(self):
        text = CLAUDE_COMMAND.read_text()

        for skill_root in (
            ".agents/skills",
            "~/.agents/skills",
            "*/.agents/skills",
        ):
            with self.subTest(skill_root=skill_root):
                self.assertIn(
                    f"Bash({skill_root}/beads-blocker-review/scripts/"
                    "list-actionable-human-beads.py:*)",
                    text,
                )

        for permission in (
            "Bash(bd gate:*)",
            "Bash(bd dep:*)",
            "Bash(bd ready:*)",
        ):
            with self.subTest(permission=permission):
                self.assertIn(permission, text)


if __name__ == "__main__":
    unittest.main()
