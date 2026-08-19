#!/usr/bin/env python3
"""Regression tests for cross-agent research-report location policy."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "AGENTS.md"
DOCUMENTATION_SKILL = ROOT / ".agents/skills/documentation-updates/SKILL.md"
COMPARISON_SKILL = ROOT / ".agents/skills/comparing-open-source-projects/SKILL.md"
REPORTING_CONTRACT = (
    ROOT
    / ".agents/skills/comparing-open-source-projects/references/reporting.md"
)


class TestResearchReportLocations(unittest.TestCase):
    def test_project_policy_sets_cross_agent_default(self):
        text = POLICY.read_text()
        self.assertIn("## Research reports", text)
        self.assertIn("`docs/research/` relative to the current repository root", text)
        self.assertIn("focused workflow may specify a\ndifferent location", text)

    def test_documentation_skill_reinforces_default_without_overriding_context(self):
        text = DOCUMENTATION_SKILL.read_text()
        self.assertIn("## Research reports", text)
        self.assertIn("`docs/research/` relative to the current repository root", text)
        self.assertIn("specified by the user, the repository, or a focused workflow", text)

    def test_comparison_skill_uses_durable_report_directory(self):
        text = COMPARISON_SKILL.read_text()
        self.assertIn("`docs/research/` in the current Git repository", text)
        self.assertNotIn("under `tmp/`", text)

    def test_reporting_contract_builds_and_validates_docs_research_path(self):
        text = REPORTING_CONTRACT.read_text()
        self.assertIn('report_dir="$repo_root/docs/research"', text)
        self.assertIn('mkdir -p "$report_dir"', text)
        self.assertIn('html_report="$report_dir/foss-comparison-', text)
        self.assertIn("inside `$repo_root/docs/research/`", text)
        self.assertNotIn("$repo_root/tmp", text)


if __name__ == "__main__":
    unittest.main()
