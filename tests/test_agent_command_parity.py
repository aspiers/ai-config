#!/usr/bin/env python3
"""Contract tests for shared Pi and Codex prompt templates."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
PI_PROMPTS = ROOT / ".pi/agent/prompts"
CODEX_PROMPTS = ROOT / ".codex/prompts"
CODEX_LINK_PREFIX = Path("../../.pi/agent/prompts")


class TestAgentCommandParity(unittest.TestCase):
    def test_codex_exposes_every_pi_prompt(self):
        pi_names = {path.name for path in PI_PROMPTS.glob("*.md")}
        codex_names = {path.name for path in CODEX_PROMPTS.glob("*.md")}

        self.assertEqual(pi_names, codex_names)

    def test_codex_prompts_link_to_pi_sources(self):
        for pi_prompt in PI_PROMPTS.glob("*.md"):
            codex_prompt = CODEX_PROMPTS / pi_prompt.name
            with self.subTest(prompt=pi_prompt.name):
                self.assertTrue(codex_prompt.is_symlink())
                self.assertEqual(
                    codex_prompt.readlink(),
                    CODEX_LINK_PREFIX / pi_prompt.name,
                )
                self.assertEqual(codex_prompt.resolve(), pi_prompt.resolve())

    def test_shared_frontmatter_is_valid(self):
        for prompt in PI_PROMPTS.glob("*.md"):
            with self.subTest(prompt=prompt.name):
                text = prompt.read_text()
                self.assertTrue(text.startswith("---\n"))
                metadata = yaml.safe_load(text.split("---", 2)[1]) or {}
                self.assertIsInstance(metadata.get("description"), str)

    def test_shared_prompts_avoid_platform_specific_expansion(self):
        forbidden = ("`ask_user`", "`ToolSearch`", "!`")
        for prompt in PI_PROMPTS.glob("*.md"):
            text = prompt.read_text()
            for marker in forbidden:
                with self.subTest(prompt=prompt.name, marker=marker):
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
