#!/usr/bin/env python3
"""Contract tests for accessible FOSS comparison matrices."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/comparing-open-source-projects/SKILL.md"
REPORTING = (
    ROOT
    / ".agents/skills/comparing-open-source-projects/references/reporting.md"
)
TEMPLATE = (
    ROOT / ".agents/skills/comparing-open-source-projects/assets/report-template.html"
)
PACKAGE_REPORTING = (
    ROOT / ".agents/skills/managing-pi-packages/references/reporting.md"
)
RATINGS = ("good", "caution", "poor", "unknown")


class TestFossComparisonReporting(unittest.TestCase):
    def test_skill_routes_multi_matrix_and_traffic_light_requirements(self):
        text = SKILL.read_text()
        self.assertIn("Add focused\nmatrices for distinct facets", text)
        self.assertIn("accessible traffic-light ratings", text)
        self.assertIn("leave non-ordinal facts uncoloured", text)

    def test_reporting_contract_defines_optional_facet_matrices(self):
        text = REPORTING.read_text()
        self.assertIn("## Additional facet matrices", text)
        self.assertIn('id="comparison-facet-SLUG"', text)
        self.assertIn("one or\nmore focused matrices", text)
        self.assertIn("do not manufacture an aggregate score", text)

    def test_reporting_contract_defines_accessible_rating_semantics(self):
        text = REPORTING.read_text()
        for rating in RATINGS:
            self.assertIn(f"`rating-{rating}`", text)
        self.assertIn("colour is supplementary", text)
        self.assertIn("Leave factual or categorical cells uncoloured", text)
        self.assertIn("visible traffic-light legend", text)

    def test_template_styles_summary_cells_and_supplies_a_legend(self):
        text = TEMPLATE.read_text()
        for rating in RATINGS:
            self.assertIn(f".rating-{rating}", text)
            self.assertIn(f'rating-key rating-{rating}', text)
        self.assertIn('class="rating-cell {{DOMAIN_FIT_RATING}}"', text)
        self.assertIn('class="rating-cell {{MAINTENANCE_RATING}}"', text)
        self.assertIn('class="rating-cell {{RECOMMENDATION_RATING}}"', text)
        self.assertIn('aria-label="Rating legend"', text)
        self.assertIn("Stronger / suitable", text)
        self.assertIn("Mixed / trade-off", text)
        self.assertIn("Weaker / blocker", text)
        self.assertIn("Unknown / not comparable", text)

    def test_template_offers_a_removable_facet_matrix(self):
        text = TEMPLATE.read_text()
        self.assertIn("Keep this example only when a focused facet matrix", text)
        self.assertIn('id="comparison-facet-{{FACET_SLUG}}"', text)
        self.assertIn('href="#project-{{PROJECT_SLUG}}"', text)
        self.assertIn("{{FACET_A_RATING}}", text)
        self.assertIn("{{FACET_B_RATING}}", text)

    def test_similar_package_audit_matrix_retains_traffic_light_badges(self):
        text = PACKAGE_REPORTING.read_text()
        expected = {
            "#22c55e": "Appears safe",
            "#f59e0b": "with caution",
            "#ef4444": "Do not",
            "#a78bfa": "Inconclusive",
        }
        for colour, label in expected.items():
            self.assertIn(colour, text)
            self.assertIn(label, text)


if __name__ == "__main__":
    unittest.main()
