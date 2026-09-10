import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents/skills/upstreaming-status"
SKILL = SKILL_DIR / "SKILL.md"
RENDERER = SKILL_DIR / "scripts/render-report.py"
TEMPLATE = SKILL_DIR / "assets/report.html"


class UpstreamingStatusSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SKILL.read_text()

    def test_frontmatter_routes_upstreaming_status_requests(self) -> None:
        self.assertRegex(self.text, r"(?m)^name: upstreaming-status$")
        self.assertIn(
            "compact terminal table plus a browser-rendered HTML report", self.text
        )
        self.assertIn("ahead/behind counts", self.text)
        self.assertIn("change-request status", self.text)

    def test_report_contract_is_progress_ordered_and_wt_inspired(self) -> None:
        self.assertIn("Order rows from least progress to furthest progress", self.text)
        self.assertIn("`↑<branch-only> ↓<upstream-only>`", self.text)
        self.assertIn(
            "| Branch and purpose | `<upstream-ref>` ↕ | Upstream progress | Next step |",
            self.text,
        )
        self.assertIn("Always return the compact table in chat", self.text)
        self.assertIn("scripts/render-report.py", self.text)
        self.assertRegex(self.text, r"temporary\s+`\.html` file outside the repository")
        self.assertIn("sentence-length description", self.text)
        self.assertIn("dependencies", self.text)
        self.assertIn("machete_graph", self.text)
        self.assertIn("Git Machete graph in a separate preformatted section", self.text)
        emoji_positions = [
            self.text.index(emoji)
            for emoji in ("⚪", "🟡", "📝", "🔴", "🟢", "⛔", "✅")
        ]
        self.assertEqual(emoji_positions, sorted(emoji_positions))
        self.assertIn("not an upstream submission branch", self.text)

    def test_related_skills_are_linked_and_exist(self) -> None:
        links = re.findall(r"\]\((\.\./[^)]+/SKILL\.md)\)", self.text)
        for expected in (
            "../checking-upstream/SKILL.md",
            "../open-in-user-browser/SKILL.md",
            "../submitting-upstream/SKILL.md",
        ):
            self.assertIn(expected, links)
        for link in set(links):
            self.assertTrue((SKILL.parent / link).resolve().is_file(), link)

    def test_renderer_and_template_exist(self) -> None:
        self.assertTrue(RENDERER.is_file())
        self.assertTrue(TEMPLATE.is_file())
        self.assertTrue(RENDERER.stat().st_mode & 0o111)


class UpstreamingStatusRendererTests(unittest.TestCase):
    def render(self, branches: list[dict]) -> str:
        data = {
            "repository": "owner/project",
            "canonical_url": "https://example.com/owner/project",
            "upstream_ref": "origin/main",
            "as_of": "2026-09-09 18:00 UTC",
            "summary": "One branch needs action.",
            "stale": False,
            "machete_graph": "main\n|\no-fix/<unsafe>",
            "branches": branches,
            "runtime_notes": [
                "`working` is a runtime mixdown.",
                "`fix/<unsafe>` remains local; never render <script>.",
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "report.json"
            output_path = root / "report.html"
            input_path.write_text(json.dumps(data))
            subprocess.run(
                [
                    sys.executable,
                    str(RENDERER),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
            )
            return output_path.read_text()

    def test_renderer_orders_links_and_escapes_rows(self) -> None:
        rendered = self.render(
            [
                {
                    "name": "fix/merged",
                    "purpose": "already upstream",
                    "description": "This branch has already landed upstream and can now be removed locally.",
                    "dependencies": ["fix/base<&>"],
                    "ahead": 1,
                    "behind": 5,
                    "stage": "merged",
                    "progress": "merged",
                    "request": {
                        "label": "PR #40",
                        "url": "https://example.com/owner/project/pull/40",
                    },
                    "next_step": "Prune branch",
                },
                {
                    "name": "fix/<unsafe>",
                    "purpose": "keep <choices> visible",
                    "description": "Keeps <choices> visible while a custom answer is entered, making both response paths easy to compare.",
                    "dependencies": [],
                    "ahead": 5,
                    "behind": 0,
                    "stage": "published",
                    "progress": "Fork published, no PR",
                    "next_step": "Open PR",
                },
            ]
        )

        self.assertIn("Upstreaming status: owner/project", rendered)
        self.assertLess(rendered.index("🟡"), rendered.index("✅"))
        self.assertIn("↑5 ↓0", rendered)
        self.assertIn("fix/&lt;unsafe&gt;", rendered)
        self.assertNotIn("fix/<unsafe>", rendered)
        self.assertIn(
            "Keeps &lt;choices&gt; visible while a custom answer is entered, making both response paths easy to compare.",
            rendered,
        )
        self.assertNotIn("keep &lt;choices&gt; visible", rendered)
        self.assertIn('href="https://example.com/owner/project/pull/40"', rendered)
        self.assertIn("fix/base&lt;&amp;&gt;", rendered)
        self.assertIn("font-family:", rendered)
        self.assertIn("ui-monospace", rendered)
        self.assertIn("Git Machete status graph", rendered)
        self.assertIn("o-fix/&lt;unsafe&gt;", rendered)
        self.assertNotIn("o-fix/<unsafe>", rendered)
        self.assertIn("<code>working</code> is a runtime mixdown.", rendered)
        self.assertIn("<code>fix/&lt;unsafe&gt;</code> remains local", rendered)
        self.assertIn("never render &lt;script&gt;", rendered)
        self.assertNotIn("never render <script>", rendered)
        self.assertNotRegex(rendered, r"\{\{[A-Z_]+\}\}")

    def test_empty_report_hides_the_table(self) -> None:
        rendered = self.render([])

        self.assertIn("No source branches qualify.", rendered)
        self.assertIn('class="table-wrap hidden"', rendered)


if __name__ == "__main__":
    unittest.main()
