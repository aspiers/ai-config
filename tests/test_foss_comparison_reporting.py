#!/usr/bin/env python3
"""Contract tests for accessible FOSS comparison matrices."""

from html.parser import HTMLParser
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
LEGEND_LABELS = {
    "rating-good": "Stronger / suitable",
    "rating-caution": "Mixed / trade-off",
    "rating-poor": "Weaker / blocker",
    "rating-unknown": "Unknown / not comparable",
}


class RatingLegendParser(HTMLParser):
    """Collect each legend key's rendered text, keyed by its rating class.

    Matching the raw template source breaks whenever an HTML formatter
    reflows a label across lines, although the browser renders the same
    text, so compare whitespace-collapsed text instead.
    """

    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, str] = {}
        self._rating: str | None = None
        self._nested_spans = 0
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "span":
            return
        if self._rating:
            self._nested_spans += 1
            return
        classes = (dict(attrs).get("class") or "").split()
        if "rating-key" in classes:
            self._rating = next(
                c for c in classes if c.startswith("rating-") and c != "rating-key"
            )
            self._text = []

    def handle_endtag(self, tag):
        if tag != "span" or not self._rating:
            return
        if self._nested_spans:
            self._nested_spans -= 1
            return
        self.labels[self._rating] = " ".join("".join(self._text).split())
        self._rating = None

    def handle_data(self, data):
        if self._rating:
            self._text.append(data)


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
        self.assertIn('class="rating-cell {{DOMAIN_FIT_RATING}}"', text)
        self.assertIn('class="rating-cell {{MAINTENANCE_RATING}}"', text)
        self.assertIn('class="rating-cell {{RECOMMENDATION_RATING}}"', text)
        self.assertIn('aria-label="Rating legend"', text)
        legend = RatingLegendParser()
        legend.feed(text)
        self.assertEqual(LEGEND_LABELS, legend.labels)

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
