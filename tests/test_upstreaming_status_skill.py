import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/upstreaming-status/SKILL.md"


class UpstreamingStatusSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SKILL.read_text()

    def test_frontmatter_routes_upstreaming_status_requests(self) -> None:
        self.assertRegex(self.text, r"(?m)^name: upstreaming-status$")
        self.assertIn("local Git branches", self.text)
        self.assertIn("ahead/behind counts", self.text)
        self.assertIn("pull-request or merge-request status", self.text)

    def test_report_contract_is_progress_ordered_and_wt_inspired(self) -> None:
        self.assertIn("Order rows from least progress to furthest progress", self.text)
        self.assertIn("`↑<branch-only> ↓<upstream-only>`", self.text)
        self.assertIn(
            "| Branch and purpose | `<upstream-ref>` ↕ | Upstream progress | Next step |",
            self.text,
        )
        emoji_positions = [
            self.text.index(emoji)
            for emoji in ("⚪", "🟡", "📝", "🔴", "🟢", "⛔", "✅")
        ]
        self.assertEqual(emoji_positions, sorted(emoji_positions))
        self.assertIn("not an upstream submission branch", self.text)

    def test_related_skills_are_linked_and_exist(self) -> None:
        links = re.findall(r"\]\((\.\./[^)]+/SKILL\.md)\)", self.text)
        self.assertIn("../checking-upstream/SKILL.md", links)
        self.assertIn("../submitting-upstream/SKILL.md", links)
        for link in set(links):
            self.assertTrue((SKILL.parent / link).resolve().is_file(), link)


if __name__ == "__main__":
    unittest.main()
