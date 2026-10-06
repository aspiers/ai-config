#!/usr/bin/env python3
"""Contract tests: every harness loads the shared global rules file."""

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / ".agents/AGENTS.md"
DEPLOYED_RULES = "~/.agents/AGENTS.md"
CODEX_BUILD = ROOT / "bin/codex-global-agents-md"

# Codex caps project AGENTS.md content at 32 KiB by default, and its docs
# disagree on whether the global file counts. Even if it does, 6 KiB of rules
# plus the style and this repository's AGENTS.md (about 16 KiB) fit.
MAX_RULES_BYTES = 6144


class TestGlobalRulesParity(unittest.TestCase):
    def test_rules_file_is_concise(self):
        self.assertLessEqual(len(RULES.read_bytes()), MAX_RULES_BYTES)

    def test_rules_have_no_trailing_whitespace(self):
        for number, line in enumerate(RULES.read_text().splitlines(), 1):
            with self.subTest(line=number):
                self.assertEqual(line, line.rstrip())

    def test_claude_code_imports_rules(self):
        claude_md = ROOT / ".claude/CLAUDE.md"
        imports = re.findall(r"^@(\S+)", claude_md.read_text(), re.MULTILINE)
        # Claude Code resolves imports relative to the importing file.
        resolved = {(claude_md.parent / path).resolve() for path in imports}
        self.assertIn(RULES.resolve(), resolved)

    def test_pi_agent_dir_links_to_rules(self):
        pi_agents_md = ROOT / ".pi/agent/AGENTS.md"
        self.assertTrue(pi_agents_md.is_symlink())
        self.assertEqual(pi_agents_md.resolve(), RULES.resolve())

    def test_opencode_instructions_include_rules(self):
        config_path = ROOT / ".config/opencode/opencode.json"
        config = json.loads(config_path.read_text())
        self.assertIn(DEPLOYED_RULES, config.get("instructions", []))

    def test_codex_global_file_concatenates_style_and_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp, "codex")
            codex_home.mkdir()
            style = Path(tmp, "style.md")
            style.write_text("STYLE BODY\n")
            env = os.environ | {
                "CODEX_HOME": str(codex_home),
                "AGENTS_GLOBAL_RULES": str(RULES),
            }

            subprocess.run([CODEX_BUILD, style], env=env, check=True,
                           capture_output=True)
            # A bare re-run, as after editing the rules, keeps the style.
            subprocess.run([CODEX_BUILD], env=env, check=True,
                           capture_output=True)

            built = (codex_home / "AGENTS.md").read_text()
            self.assertIn("STYLE BODY\n", built)
            self.assertTrue(built.endswith(RULES.read_text()))


if __name__ == "__main__":
    unittest.main()
