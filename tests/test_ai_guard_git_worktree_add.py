#!/usr/bin/env python3
"""
Test suite for the ai-guard-git-worktree-add PreToolUse hook.

Checks that raw `git worktree add` is denied in the shapes agents write it,
and that mentions of it in arguments, other git worktree subcommands and
the explicit override are allowed.
"""

import json
import os
import subprocess
import unittest
from pathlib import Path

GUARD = Path(__file__).parent.parent / "bin" / "ai-guard-git-worktree-add"


def decide(command: str, env: dict[str, str] | None = None) -> str:
    """Return "deny" or "allow" for a Bash tool call running `command`."""
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    run_env = {k: v for k, v in os.environ.items() if k != "AI_ALLOW_GIT_WORKTREE_ADD"}
    run_env.update(env or {})
    result = subprocess.run(
        [str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        env=run_env,
        check=True,
    )
    if not result.stdout.strip():
        return "allow"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


class TestAiGuardGitWorktreeAdd(unittest.TestCase):
    def test_denies_raw_worktree_add(self):
        for command in [
            "git worktree add .worktrees/x -b x master",
            "git -C /repo worktree add ../x",
            "git -c core.hooksPath=/dev/null worktree add ../x",
            "cd /repo && git worktree add ../x 2>&1 | tail -2",
            "echo start; git worktree add ../x",
            "set -e\ngit worktree add ../x",
            "/usr/bin/git worktree add ../x",
            "command git worktree add ../x",
            "FOO=1 git worktree add ../x",
            "T=$(mktemp -d) && git worktree add --detach $T HEAD",
        ]:
            with self.subTest(command=command):
                self.assertEqual(decide(command), "deny")

    def test_allows_other_commands(self):
        for command in [
            "git worktree list",
            "git worktree remove --force ../x",
            "wt switch --create x --base origin/main",
            'grep -rn "git worktree add" docs/',
            "echo 'git worktree add'",
            "git commit -m 'avoid git worktree add'",
            "git status",
            "",
        ]:
            with self.subTest(command=command):
                self.assertEqual(decide(command), "allow")

    def test_override_prefix_allows(self):
        self.assertEqual(
            decide("AI_ALLOW_GIT_WORKTREE_ADD=1 git worktree add --detach /tmp/x HEAD"),
            "allow",
        )

    def test_override_applies_only_to_its_own_command(self):
        self.assertEqual(
            decide("AI_ALLOW_GIT_WORKTREE_ADD=1 true; git worktree add ../x"), "deny"
        )

    def test_override_env_allows(self):
        self.assertEqual(
            decide("git worktree add ../x", {"AI_ALLOW_GIT_WORKTREE_ADD": "1"}), "allow"
        )

    def test_ignores_non_bash_input(self):
        result = subprocess.run(
            [str(GUARD)],
            input=json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}}),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")

    def test_deny_reason_names_the_skill(self):
        payload = json.dumps({"tool_input": {"command": "git worktree add ../x"}})
        out = subprocess.run(
            [str(GUARD)], input=payload, capture_output=True, text=True, check=True
        ).stdout
        self.assertIn(
            "git-branch-management",
            json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"],
        )


if __name__ == "__main__":
    unittest.main()
