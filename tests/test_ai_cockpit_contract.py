#!/usr/bin/env python3
"""Validation for the public-safe portable AI cockpit contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = ROOT / "deploy" / "ai-cockpit"
README = DEPLOY_DIR / "README.md"
ENV_EXAMPLE = DEPLOY_DIR / "env.example"

EXPECTED_VOLUMES = {
    "cockpit-home",
    "cockpit-herdr",
    "cockpit-collie",
    "cockpit-agentbox",
    "cockpit-tailscale",
    "cockpit-repos",
    "cockpit-backups",
}


class TestAiCockpitContract(unittest.TestCase):
    """Keep the target-neutral contract complete and free of instance data."""

    def setUp(self) -> None:
        self.readme = README.read_text(encoding="utf-8")
        self.env = ENV_EXAMPLE.read_text(encoding="utf-8")

    def test_required_contract_sections_exist(self) -> None:
        headings = {
            "## Runtime Identity and Layout",
            "## Components and Supervision",
            "## Network Contract",
            "## Secret Injection",
            "## Health Contract",
            "## Startup and Recovery",
            "## Backup and Restore",
            "## Client Contract",
            "## Target-Neutral Acceptance Matrix",
            "## Deployment Decision Gate",
        }
        self.assertEqual(
            headings,
            {heading for heading in headings if heading in self.readme},
        )

    def test_runtime_prohibitions_are_explicit(self) -> None:
        self.assertIn("MUST NOT run local AgentBox boxes", self.readme)
        self.assertIn("mount a Docker socket", self.readme)
        self.assertIn("Funnel is forbidden", self.readme)
        self.assertNotIn("/var/run/docker.sock", self.readme)

    def test_every_named_volume_appears_in_contract_and_template(self) -> None:
        for volume in EXPECTED_VOLUMES:
            with self.subTest(volume=volume):
                self.assertIn(volume, self.readme)
                self.assertIn(volume, self.env)

    def test_env_inventory_has_unique_placeholder_assignments(self) -> None:
        assignments: dict[str, str] = {}
        for line_number, line in enumerate(self.env.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            self.assertRegex(stripped, r"^[A-Z][A-Z0-9_]*=\S+$")
            key, value = stripped.split("=", 1)
            self.assertNotIn(key, assignments, f"duplicate variable on line {line_number}")
            assignments[key] = value

        secret_paths = {
            key: value for key, value in assignments.items() if key.endswith("_SECRET_FILE")
        }
        self.assertGreater(len(secret_paths), 0)
        for key, value in secret_paths.items():
            with self.subTest(variable=key):
                self.assertTrue(value.startswith("/run/secrets/"))

    def test_public_files_contain_no_instance_identifiers(self) -> None:
        public_text = f"{self.readme}\n{self.env}"
        forbidden = {
            "home directory": r"/home/[A-Za-z0-9._-]+/",
            "email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "currency amount": r"(?:[$€£]\s?\d|\d\s?(?:USD|EUR|GBP)\b)",
            "private repository URL": r"(?:git@|ssh://|https://)[^\s)]+\.git\b",
        }
        for label, pattern in forbidden.items():
            with self.subTest(identifier=label):
                self.assertIsNone(re.search(pattern, public_text, re.IGNORECASE))

        addresses = set(re.findall(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}", public_text))
        self.assertLessEqual(addresses, {"127.0.0.1"})


if __name__ == "__main__":
    unittest.main()
