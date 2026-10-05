#!/usr/bin/env python3
"""
Test suite for the ai-guard-hidden-question-context Claude Code hook.

Builds synthetic transcripts in the block shapes Claude Code records and
checks that a questionnaire preceded only by a hidden progress update is
denied once, that the following stop is blocked once, and that everything
else is allowed.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).parent.parent / "bin" / "ai-guard-hidden-question-context"
SESSION = "session-1"


def assistant(*blocks: dict, msg_id: str = "msg_1") -> dict:
    return {"type": "assistant", "message": {"id": msg_id, "content": list(blocks)}}


def thinking(text: str = "") -> dict:
    return {"type": "thinking", "thinking": text, "signature": "sig"}


def text(body: str) -> dict:
    return {"type": "text", "text": body}


def tool_use(name: str = "AskUserQuestion", tool_id: str = "toolu_ask") -> dict:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": {}}


def tool_result() -> dict:
    return {
        "type": "user",
        "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_prev"}]},
    }


ATTACHMENT = {"type": "attachment"}
HIDDEN_NOTE = "I've drafted a comment for the PR raising an edge case."


class TestAiGuardHiddenQuestionContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.transcript = self.dir / "transcript.jsonl"
        self.env = {**os.environ, "AI_GUARD_STATE_DIR": str(self.dir / "state")}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *entries: dict) -> None:
        # Claude Code stores each content block of a message as its own line.
        lines = []
        for entry in entries:
            if entry["type"] == "assistant":
                for block in entry["message"]["content"]:
                    lines.append(assistant(block, msg_id=entry["message"]["id"]))
            else:
                lines.append(entry)
        self.transcript.write_text("".join(json.dumps(e) + "\n" for e in lines))

    def run_hook(self, event: dict) -> dict | None:
        payload = {"session_id": SESSION, "transcript_path": str(self.transcript), **event}
        result = subprocess.run(
            [str(GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.env,
            check=True,
            timeout=10,
        )
        return json.loads(result.stdout) if result.stdout.strip() else None

    def ask(self, tool_id: str = "toolu_ask") -> str:
        out = self.run_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "AskUserQuestion",
                "tool_input": {},
                "tool_use_id": tool_id,
            }
        )
        return out["hookSpecificOutput"]["permissionDecision"] if out else "allow"

    def stop(self) -> str:
        out = self.run_hook({"hook_event_name": "Stop", "stop_hook_active": False})
        return out["decision"] if out else "allow"

    def test_denies_question_after_hidden_progress_update(self):
        self.write(tool_result(), ATTACHMENT, assistant(thinking(), thinking(HIDDEN_NOTE), tool_use()))
        self.assertEqual(self.ask(), "deny")

    def test_allows_question_after_visible_text(self):
        self.write(tool_result(), assistant(thinking(), text("Here is the draft."), tool_use()))
        self.assertEqual(self.ask(), "allow")

    def test_allows_question_with_nothing_written_before_it(self):
        self.write(tool_result(), assistant(thinking(), tool_use()))
        self.assertEqual(self.ask(), "allow")

    def test_only_considers_output_since_last_user_entry(self):
        self.write(
            assistant(thinking(HIDDEN_NOTE), tool_use("Bash", "toolu_prev"), msg_id="msg_0"),
            tool_result(),
            assistant(thinking(), text("Visible summary."), tool_use()),
        )
        self.assertEqual(self.ask(), "allow")

    def test_ignores_other_tools(self):
        self.write(tool_result(), assistant(thinking(HIDDEN_NOTE), tool_use("Bash", "toolu_bash")))
        out = self.run_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "ls"},
                "tool_use_id": "toolu_bash",
            }
        )
        self.assertIsNone(out)

    def test_fails_open_when_call_never_reaches_transcript(self):
        self.write(tool_result(), assistant(thinking(HIDDEN_NOTE), tool_use()))
        self.assertEqual(self.ask(tool_id="toolu_missing"), "allow")

    def test_fails_open_without_transcript(self):
        self.assertEqual(self.ask(), "allow")

    def test_full_cycle_denies_once_blocks_stop_once_then_allows(self):
        self.write(tool_result(), assistant(thinking(), thinking(HIDDEN_NOTE), tool_use()))
        self.assertEqual(self.ask(), "deny")
        self.assertEqual(self.stop(), "block")
        # The re-ask is often preceded by another hidden note; it must pass.
        self.write(tool_result(), assistant(thinking("Asking now."), tool_use(tool_id="toolu_2")))
        self.assertEqual(self.ask(tool_id="toolu_2"), "allow")
        self.assertEqual(self.stop(), "allow")

    def test_immediate_reask_after_deny_is_allowed(self):
        self.write(tool_result(), assistant(thinking(HIDDEN_NOTE), tool_use()))
        self.assertEqual(self.ask(), "deny")
        self.assertEqual(self.ask(), "allow")
        self.assertEqual(self.stop(), "allow")

    def test_stop_without_prior_deny_is_allowed(self):
        self.assertEqual(self.stop(), "allow")

    def test_stale_state_is_ignored(self):
        state = self.dir / "state" / f"{SESSION}.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"phase": "denied", "time": 0}))
        self.assertEqual(self.stop(), "allow")
        self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
