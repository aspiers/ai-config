#!/usr/bin/env python3
"""
Test suite for the ai-guard-orca-unread-mail stop hook.

Runs the guard against a fake Orca CLI and checks that unread mail blocks a
stop once per message, without marking it read, and that everything else
allows the stop.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).parent.parent / "bin" / "ai-guard-orca-unread-mail"
HANDLE = "term_coordinator"
REPORT = {
    "id": "msg_1",
    "from_handle": "term_worker",
    "type": "status",
    "subject": "Branch ready to merge",
}


class TestAiGuardOrcaUnreadMail(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.mailbox = self.dir / "mailbox.json"
        self.calls = self.dir / "calls.log"
        fake = self.dir / "orca"
        fake.write_text(
            "#!/bin/sh\n"
            f'echo "$*" >> "{self.calls}"\n'
            f'cat "{self.mailbox}"\n'
        )
        fake.chmod(0o755)
        self.env = {
            **os.environ,
            "ORCA_CLI": str(fake),
            "ORCA_TERMINAL_HANDLE": HANDLE,
            "AI_GUARD_STATE_DIR": str(self.dir / "state"),
        }
        self.set_mail(REPORT)

    def tearDown(self):
        self.tmp.cleanup()

    def set_mail(self, *messages: dict) -> None:
        result = {"messages": list(messages), "count": len(messages)}
        self.mailbox.write_text(json.dumps({"ok": True, "result": result}))

    def run_guard(self, event: dict | None = None, *args: str) -> str:
        stdin = "" if event is None else json.dumps(event)
        return subprocess.run(
            [str(GUARD), *args],
            input=stdin,
            capture_output=True,
            text=True,
            env=self.env,
            check=True,
        ).stdout

    def test_unread_mail_blocks_stop_and_lists_it(self):
        output = json.loads(self.run_guard({"hook_event_name": "Stop"}))
        self.assertEqual(output["decision"], "block")
        self.assertIn("status from term_worker: Branch ready to merge", output["reason"])

    def test_peeks_without_marking_read(self):
        self.run_guard({"hook_event_name": "Stop"})
        self.assertEqual(
            self.calls.read_text().split(),
            ["orchestration", "check", "--terminal", HANDLE, "--peek", "--json"],
        )

    def test_each_message_blocks_only_once(self):
        self.assertTrue(self.run_guard({}))
        self.assertEqual(self.run_guard({}), "")
        self.set_mail(REPORT, {**REPORT, "id": "msg_2", "subject": "Question"})
        reason = json.loads(self.run_guard({}))["reason"]
        self.assertIn("2 unread", reason)

    def test_continued_stop_is_allowed(self):
        self.assertEqual(self.run_guard({"stop_hook_active": True}), "")

    def test_empty_mailbox_allows_stop(self):
        self.set_mail()
        self.assertEqual(self.run_guard({}), "")

    def test_outside_orca_allows_stop(self):
        del self.env["ORCA_TERMINAL_HANDLE"]
        self.assertEqual(self.run_guard({}), "")
        self.assertFalse(self.calls.exists())

    def test_cli_failure_allows_stop(self):
        self.mailbox.write_text("not json")
        self.assertEqual(self.run_guard({}), "")

    def test_text_mode_prints_plain_reason(self):
        output = self.run_guard(None, "--text")
        self.assertTrue(output.startswith("1 unread Orca message(s)"))


if __name__ == "__main__":
    unittest.main()
