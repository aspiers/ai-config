#!/usr/bin/env python3
"""
Test suite for the ai-guard-stale-bug-report PreToolUse hook.

Builds throwaway git repositories and checks that `bd create --type=bug` is
denied only while HEAD lacks commits from the trunk, and that other bd
commands, other issue types and the override are allowed.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).parent.parent / "bin" / "ai-guard-stale-bug-report"
BUG = "bd create --type=bug --priority=1 --title='Stuck' --body-file - <<'EOF'\nx\nEOF"


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def commit(cwd: Path, message: str) -> None:
    git(cwd, "commit", "-q", "--allow-empty", "-m", message)


def decide(command: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    """Return "deny" or "allow" for a Bash tool call running `command`."""
    payload = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    )
    run_env = {k: v for k, v in os.environ.items() if k != "AI_ALLOW_STALE_BUG_REPORT"}
    run_env.update(env or {})
    result = subprocess.run(
        [str(GUARD)], input=payload, capture_output=True, text=True, env=run_env, check=True
    )
    if not result.stdout.strip():
        return "allow"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


class TestAiGuardStaleBugReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "T")
        commit(self.repo, "base")
        git(self.repo, "switch", "-q", "-c", "feature")
        commit(self.repo, "feature work")

    def tearDown(self):
        self.tmp.cleanup()

    def advance_main(self):
        git(self.repo, "switch", "-q", "main")
        commit(self.repo, "fix on trunk")
        git(self.repo, "switch", "-q", "feature")

    def test_denies_bug_when_behind_local_trunk(self):
        self.advance_main()
        for command in [
            BUG,
            "bd create -t bug --title=x",
            "bd new --type bug --title=x",
            "bd create --title=x --type=BUG 2>&1 | tail",
            "cd . && bd create --type=bug --title=x",
        ]:
            with self.subTest(command=command):
                self.assertEqual(decide(command, self.repo), "deny")

    def test_denies_when_behind_origin_trunk(self):
        origin = Path(self.tmp.name) / "origin.git"
        git(self.repo, "init", "-q", "--bare", str(origin))
        git(self.repo, "push", "-q", str(origin), "main")
        git(self.repo, "remote", "add", "origin", str(origin))
        git(self.repo, "fetch", "-q", "origin")
        clone = Path(self.tmp.name) / "clone"
        subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True)
        git(clone, "config", "user.email", "t@example.com")
        git(clone, "config", "user.name", "T")
        commit(clone, "fix on trunk")
        git(clone, "push", "-q", "origin", "main")
        git(self.repo, "fetch", "-q", "origin")
        self.assertEqual(decide(BUG, self.repo), "deny")

    def test_reason_names_trunk_and_skill(self):
        self.advance_main()
        payload = json.dumps({"tool_input": {"command": BUG}, "cwd": str(self.repo)})
        out = subprocess.run(
            [str(GUARD)], input=payload, capture_output=True, text=True, check=True
        ).stdout
        text = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("1 commit(s) behind main", text)
        self.assertIn("beads-best-practices", text)

    def test_allows_bug_when_current(self):
        self.assertEqual(decide(BUG, self.repo), "allow")

    def test_allows_other_commands_when_behind(self):
        self.advance_main()
        for command in [
            "bd create --type=task --title=x",
            "bd create --title='bug in parser'",
            "bd list --type=bug",
            "bd show x",
            "echo 'bd create --type=bug'",
            "git status",
            "",
        ]:
            with self.subTest(command=command):
                self.assertEqual(decide(command, self.repo), "allow")

    def test_override_prefix_allows(self):
        self.advance_main()
        self.assertEqual(decide(f"AI_ALLOW_STALE_BUG_REPORT=1 {BUG}", self.repo), "allow")

    def test_override_applies_only_to_its_own_command(self):
        self.advance_main()
        self.assertEqual(
            decide("AI_ALLOW_STALE_BUG_REPORT=1 true; bd create -t bug", self.repo), "deny"
        )

    def test_override_env_allows(self):
        self.advance_main()
        self.assertEqual(
            decide(BUG, self.repo, {"AI_ALLOW_STALE_BUG_REPORT": "1"}), "allow"
        )

    def test_allows_outside_git(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        self.assertEqual(decide(BUG, plain), "allow")


if __name__ == "__main__":
    unittest.main()
