#!/usr/bin/env python3
"""
Tests for bin/orca-project-group and the runtime_call helper it uses from
bin/orca_cli.py: grouping repos by project group, resolving a group by name,
and the one-line JSON exchange with Orca's runtime socket.
"""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
import tempfile
import threading
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

BIN_DIR = Path(__file__).parents[1] / "bin"
SCRIPT = BIN_DIR / "orca-project-group"
sys.path.insert(0, str(BIN_DIR))
SPEC = importlib.util.spec_from_loader(
    "orca_project_group",
    SourceFileLoader("orca_project_group", str(SCRIPT)),
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

import orca_cli  # noqa: E402

GROUPS = [{"id": "g1", "name": "tools"}, {"id": "g2", "name": "work"}]


class MembersTests(unittest.TestCase):
    def test_lists_members_and_ungrouped_last(self) -> None:
        repos = [
            {"path": "/b", "projectGroupId": "g1"},
            {"path": "/a", "projectGroupId": "g1"},
            {"path": "/c", "projectGroupId": None},
            {"path": "/d", "projectGroupId": "deleted-group"},
        ]
        self.assertEqual(
            MODULE.members_by_group(GROUPS, repos),
            [
                {"id": "g1", "name": "tools", "repos": ["/a", "/b"]},
                {"id": "g2", "name": "work", "repos": []},
                {"id": None, "name": None, "repos": ["/c", "/d"]},
            ],
        )


class ResolveGroupTests(unittest.TestCase):
    def test_accepts_name_or_id(self) -> None:
        self.assertEqual(MODULE.resolve_group(GROUPS, "work"), "g2")
        self.assertEqual(MODULE.resolve_group(GROUPS, "g1"), "g1")

    def test_none_ungroups(self) -> None:
        self.assertIsNone(MODULE.resolve_group(GROUPS, "none"))

    def test_rejects_unknown_and_ambiguous_names(self) -> None:
        with self.assertRaises(SystemExit):
            MODULE.resolve_group(GROUPS, "missing")
        with self.assertRaises(SystemExit):
            MODULE.resolve_group([*GROUPS, {"id": "g3", "name": "work"}], "work")


class RuntimeCallTests(unittest.TestCase):
    def serve_once(self, path: str, reply: dict, seen: list) -> threading.Thread:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(path)
        server.listen(1)

        def handle() -> None:
            connection, _ = server.accept()
            with connection, connection.makefile("rb") as lines:
                seen.append(json.loads(lines.readline()))
                connection.sendall((json.dumps(reply) + "\n").encode())
            server.close()

        thread = threading.Thread(target=handle)
        thread.start()
        return thread

    def call(self, reply: dict, seen: list) -> object:
        with tempfile.TemporaryDirectory() as config_home:
            endpoint = str(Path(config_home) / "rt.sock")
            (Path(config_home) / "orca").mkdir()
            (Path(config_home) / "orca" / "orca-runtime.json").write_text(
                json.dumps(
                    {
                        "authToken": "secret",
                        "transports": [
                            {"kind": "websocket", "endpoint": "ws://x"},
                            {"kind": "unix", "endpoint": endpoint},
                        ],
                    }
                )
            )
            thread = self.serve_once(endpoint, reply, seen)
            try:
                with patch.dict("os.environ", {"XDG_CONFIG_HOME": config_home}):
                    return orca_cli.runtime_call("projectGroup.moveProject", {"repo": "id:r"})
            finally:
                thread.join(5)

    def test_sends_token_method_and_params(self) -> None:
        seen: list = []
        result = self.call({"id": "x", "ok": True, "result": {"done": 1}}, seen)
        self.assertEqual(result, {"done": 1})
        self.assertEqual(seen[0]["authToken"], "secret")
        self.assertEqual(seen[0]["method"], "projectGroup.moveProject")
        self.assertEqual(seen[0]["params"], {"repo": "id:r"})

    def test_raises_on_error_reply(self) -> None:
        reply = {"id": "x", "ok": False, "error": {"code": "not_found", "message": "no repo"}}
        with self.assertRaisesRegex(RuntimeError, "not_found: no repo"):
            self.call(reply, [])


if __name__ == "__main__":
    unittest.main()
