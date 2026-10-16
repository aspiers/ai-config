#!/usr/bin/env python3
"""Tests for pi-web-ensure-pi-sdk-links peer replacement."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "pi-web-ensure-pi-sdk-links"
PEERS = ("pi-coding-agent", "pi-agent-core", "pi-ai")


def write_package(path: Path, name: str) -> None:
    path.mkdir(parents=True)
    (path / "package.json").write_text(json.dumps({"name": name}, indent=2))


class TestEnsurePiSdkLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.agent = root / "agent"
        self.sdk = root / "sdk"
        write_package(self.agent / "npm/node_modules/@jmfederico/pi-web", "@jmfederico/pi-web")
        write_package(self.sdk, "@earendil-works/pi-coding-agent")
        for peer in PEERS[1:]:
            write_package(self.sdk / "node_modules/@earendil-works" / peer, f"@earendil-works/{peer}")
        self.scope = self.agent / "npm/node_modules/@earendil-works"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_script(self) -> subprocess.CompletedProcess:
        env = os.environ | {"PI_CODING_AGENT_DIR": str(self.agent), "PI_WEB_PI_SDK_ROOT": str(self.sdk)}
        return subprocess.run([SCRIPT], env=env, capture_output=True, text=True)

    def test_replaces_npm_installed_peer_copies(self) -> None:
        for peer in PEERS:
            write_package(self.scope / peer, f"@earendil-works/{peer}")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        for peer in PEERS:
            self.assertTrue((self.scope / peer).is_symlink(), peer)
        self.assertEqual((self.scope / "pi-coding-agent").resolve(), self.sdk.resolve())

    def test_refuses_foreign_directory(self) -> None:
        write_package(self.scope / "pi-coding-agent", "something-else")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Refusing to replace non-symlink", result.stderr)
        self.assertFalse((self.scope / "pi-coding-agent").is_symlink())


if __name__ == "__main__":
    unittest.main()
