#!/usr/bin/env python3
"""Contract tests for human-attention handling in background bead workflows.

The /bg, /bed and /bgp commands are thin wrappers, so these tests check that
each wrapper delegates to the right skill, and check the protocol itself in
the skill that owns it.
"""

from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    "claude": ROOT / ".claude/commands",
    "opencode": ROOT / ".config/opencode/command",
    "pi": ROOT / ".pi/agent/prompts",
}
SKILLS = ROOT / ".agents/skills"
BEST_PRACTICES = SKILLS / "beads-best-practices/SKILL.md"
SERIAL_SKILL = SKILLS / "beads-grinding/SKILL.md"
PARALLEL_SKILL = SKILLS / "beads-parallel-grinding/SKILL.md"
ONE_BEAD_ONE_DOER_LINK = "beads-best-practices/SKILL.md#one-bead-one-doer"


def read_command(platform: str, command: str) -> str:
    return (PLATFORMS[platform] / f"{command}.md").read_text()


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def section(text: str, heading: str) -> str:
    """Return the body of a level-2 heading, up to the next level-2 heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    if not match:
        raise AssertionError(f"missing section: ## {heading}")
    return match.group(1)


class TestBackgroundHumanAttention(unittest.TestCase):
    def assert_all_in(self, phrases, text):
        for phrase in phrases:
            self.assertIn(phrase, text)

    def test_serial_commands_delegate_to_grinding_skill(self):
        for platform in PLATFORMS:
            for command in ("bg", "bed"):
                with self.subTest(platform=platform, command=command):
                    text = read_command(platform, command)
                    self.assertIn("`beads-grinding` skill", text)

    def test_bed_command_selects_unattended_rules(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = read_command(platform, "bed")
                self.assertIn("**Running unattended**", text)

    def test_parallel_commands_delegate_human_protocol(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = read_command(platform, "bgp")
                self.assertIn("beads-parallel-grinding", text)
                self.assertIn("beads-best-practices", text)
                self.assertIn("human-attention queue", text)

    def test_claude_commands_allow_human_queue_operations(self):
        skills = {
            "bg": "Skill(beads-grinding)",
            "bed": "Skill(beads-grinding)",
            "bgp": "Skill(beads-parallel-grinding)",
        }
        for command, skill in skills.items():
            with self.subTest(command=command):
                metadata = frontmatter(read_command("claude", command))
                allowed = metadata["allowed-tools"]
                self.assertIn(skill, allowed)
                self.assertIn("Skill(beads-best-practices)", allowed)
                self.assertIn("Bash(bd label:*)", allowed)
                self.assertIn("Bash(bd comments:*)", allowed)
                self.assertIn("Bash(bd human:*)", allowed)

    def test_serial_skill_keeps_human_queue_out_of_agent_ready_work(self):
        text = SERIAL_SKILL.read_text()
        self.assertIn("beads-best-practices", text)
        self.assert_all_in(
            ("bd ready --exclude-label=human", "agent-ready queue is empty"),
            section(text, "Workflow") + section(text, "Rules"),
        )
        self.assert_all_in(
            (
                "bd human list --json",
                "bd ready --exclude-label=human",
                'bd label add "$ask" human',
                'bd dep add "$current" "$ask"',
                'bd update "$current" --status=open',
                ONE_BEAD_ONE_DOER_LINK,
                "Never call `bd human respond`",
            ),
            section(text, "Work that needs a person"),
        )

    def test_serial_skill_unattended_reports_human_work_without_stopping(self):
        text = section(SERIAL_SKILL.read_text(), "Running unattended")
        self.assert_all_in(
            (
                "**Never ask a question.**",
                "beads-best-practices/SKILL.md#do-not-close-around-the-human",
                "Split it into their own bead",
                "carry on with other ready work",
                "Run `bd human list` again at the end, and put it first",
                "Distinguish an empty agent-ready queue",
            ),
            text,
        )

    def test_parallel_skill_owns_orchestrator_human_transitions(self):
        text = PARALLEL_SKILL.read_text()
        self.assert_all_in(
            (
                "bd ready --exclude-label=human",
                "bd human list --json",
                'bd label add "$ask" human',
                'bd dep add "$blocked" "$ask"',
                'bd update "$blocked" --status=open',
                ONE_BEAD_ONE_DOER_LINK,
                "Only the orchestrator does this",
                "Never label the in-flight bead",
                "never call `bd human respond`",
            ),
            section(text, "Keep work that needs a person out of the agent queue"),
        )
        self.assertIn(
            "**Reported a blocker only a person can clear**",
            section(text, "When a subagent fails"),
        )

    def test_shared_best_practices_split_verify_and_clear_human_work(self):
        text = BEST_PRACTICES.read_text()
        self.assert_all_in(
            (
                "### One Bead, One Doer",
                'bd label add "$ask" human',
                'bd dep add "$work" "$ask"',
                "bd ready --exclude-label=human",
                "### Do Not Leave It `in_progress`",
                "bd human list --json",
                'bd comments add "$id"',
                'bd label remove "$id" human',
                "Never use `bd human respond`",
                "### Do Not Close Around the Human",
            ),
            section(text, "Work That Needs a Person"),
        )


if __name__ == "__main__":
    unittest.main()
