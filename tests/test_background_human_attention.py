#!/usr/bin/env python3
"""Contract tests for human-attention handling in background bead workflows."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    "claude": ROOT / ".claude/commands",
    "opencode": ROOT / ".config/opencode/command",
    "pi": ROOT / ".pi/agent/prompts",
}
BEST_PRACTICES = ROOT / ".agents/skills/beads-best-practices/SKILL.md"
PARALLEL_SKILL = ROOT / ".agents/skills/beads-parallel-grinding/SKILL.md"


def read_command(platform: str, command: str) -> str:
    return (PLATFORMS[platform] / f"{command}.md").read_text()


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


class TestBackgroundHumanAttention(unittest.TestCase):
    def test_serial_grinds_keep_human_queue_out_of_agent_ready_work(self):
        required = (
            "beads-best-practices",
            "bd ready --exclude-label=human",
            "bd human list --json",
            "bd comments add",
            "bd label add <id> human",
            "bd label remove <id> human",
            "bd update <id> --status=open",
            "Never call `bd human respond`",
            "agent-ready queue is empty",
        )
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = read_command(platform, "bg")
                for phrase in required:
                    self.assertIn(phrase, text)

    def test_unattended_bed_reports_human_work_without_stopping(self):
        required = (
            "beads-best-practices",
            "bd comments add",
            "label the waiting bead `human`",
            "bd update <id> --status=open",
            "bd human list --json",
            "continue with other agent-ready work",
            "Before the wake-up report, run `bd human list`",
        )
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = read_command(platform, "bed")
                for phrase in required:
                    self.assertIn(phrase, text)

    def test_parallel_commands_delegate_human_protocol(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = read_command(platform, "bgp")
                self.assertIn("beads-parallel-grinding", text)
                self.assertIn("beads-best-practices", text)
                self.assertIn("human-attention queue", text)

    def test_claude_commands_allow_human_queue_operations(self):
        for command in ("bg", "bgp", "bed"):
            with self.subTest(command=command):
                metadata = frontmatter(read_command("claude", command))
                allowed = metadata["allowed-tools"]
                self.assertIn("Skill(beads-best-practices)", allowed)
                self.assertIn("Bash(bd label:*)", allowed)
                self.assertIn("Bash(bd comments:*)", allowed)
                self.assertIn("Bash(bd human:*)", allowed)

    def test_parallel_skill_owns_orchestrator_human_transitions(self):
        text = PARALLEL_SKILL.read_text()
        required = (
            "bd ready --exclude-label=human",
            "bd human list --json",
            "bd comments add",
            "bd label add <id> human",
            "bd label remove <id> human",
            "bd update <id> --status=open",
            "human-only blocker",
            "Never use `bd human respond`",
        )
        for phrase in required:
            self.assertIn(phrase, text)

    def test_shared_best_practices_verify_and_clear_human_flags(self):
        text = BEST_PRACTICES.read_text()
        required = (
            "bd human list --json",
            'bd comments add "$id"',
            'bd label remove "$id" human',
            'bd update "$id" --status=open',
            "Do not use `bd human respond`",
            "Only return the bead to `in_progress`",
        )
        for phrase in required:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
