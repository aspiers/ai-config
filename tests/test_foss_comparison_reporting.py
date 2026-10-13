#!/usr/bin/env python3
"""Check FOSS research remains specialised and presentation has one owner."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FOSS = ROOT / '.agents/skills/comparing-open-source-projects'
SHARED = ROOT / '.agents/skills/matrix-comparison'
PACKAGE_REPORTING = ROOT / '.agents/skills/managing-pi-packages/references/reporting.md'


class TestFossComparisonReporting(unittest.TestCase):
    def test_foss_routes_shared_presentation(self):
        text = (FOSS / 'SKILL.md').read_text()
        self.assertIn('../matrix-comparison/SKILL.md', text)
        self.assertIn('licensing', text)
        self.assertIn('canonical primary repository', text)
        self.assertIn('common\n   window', text)
        report = (FOSS / 'references/reporting.md').read_text()
        self.assertIn('../../matrix-comparison/references/reporting.md', report)
        self.assertIn('GitHub stars', report)
        self.assertIn('Licence', report)
        self.assertIn('Maintenance', report)

    def test_legacy_template_is_the_shared_asset(self):
        old = FOSS / 'assets/report-template.html'
        self.assertTrue(old.is_symlink())
        self.assertEqual(old.resolve(), (SHARED / 'assets/report-template.html').resolve())

    def test_shared_contract_preserves_facets_and_colour_semantics(self):
        contract = (SHARED / 'references/reporting.md').read_text()
        for status in ['good', 'caution', 'poor', 'unknown', 'neutral']:
            self.assertIn(f'`{status}`', contract)
        self.assertIn('focused facet matrices', contract)
        self.assertIn('Match all selected requirements (AND)', contract)
        self.assertIn('Do not label missing evidence red', contract)

    def test_package_audit_contract_is_unchanged(self):
        text = PACKAGE_REPORTING.read_text()
        for colour, label in {'#22c55e': 'Appears safe', '#f59e0b': 'with caution',
                              '#ef4444': 'Do not', '#a78bfa': 'Inconclusive'}.items():
            self.assertIn(colour, text)
            self.assertIn(label, text)


if __name__ == '__main__':
    unittest.main()
