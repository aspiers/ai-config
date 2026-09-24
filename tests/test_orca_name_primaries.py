#!/usr/bin/env python3
"""
Test suite for the orca-name-primaries script.

Pins which workspaces get renamed (automatic-named primaries only), the name
they get (the Orca repo name), and that one failing host does not stop the
others.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

BIN_DIR = Path(__file__).parents[1] / "bin"
SCRIPT = BIN_DIR / "orca-name-primaries"
sys.path.insert(0, str(BIN_DIR))
SPEC = importlib.util.spec_from_loader(
    "orca_name_primaries",
    SourceFileLoader("orca_name_primaries", str(SCRIPT)),
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

REPOS = [{"id": "r1", "displayName": "tacticalvote"}]


def worktree(name: str, mode: str = "automatic", main: bool = True, repo: str = "r1"):
    return {
        "id": f"{repo}::/src/{name}",
        "repoId": repo,
        "displayName": name,
        "displayNameMode": mode,
        "isMainWorktree": main,
    }


class PlannedRenamesTests(unittest.TestCase):
    def test_renames_automatic_primary_to_repo_name(self) -> None:
        self.assertEqual(
            MODULE.planned_renames(REPOS, [worktree("main")]),
            [MODULE.Rename("r1::/src/main", "main", "tacticalvote")],
        )

    def test_leaves_fixed_names_and_feature_worktrees_alone(self) -> None:
        worktrees = [worktree("orca main", mode="fixed"), worktree("feature-x", main=False)]
        self.assertEqual(MODULE.planned_renames(REPOS, worktrees), [])

    def test_skips_already_named_and_unknown_repos(self) -> None:
        worktrees = [worktree("tacticalvote"), worktree("main", repo="missing")]
        self.assertEqual(MODULE.planned_renames(REPOS, worktrees), [])


class MainTests(unittest.TestCase):
    def test_failing_environment_does_not_stop_others(self) -> None:
        def fake_run_orca(args: list[str]):
            if args[:2] == ["environment", "list"]:
                return {"environments": [{"name": "down"}, {"name": "up"}]}
            if "down" in args:
                raise RuntimeError("not connected")
            if args[:2] == ["repo", "list"]:
                return {"repos": REPOS}
            if args[:2] == ["worktree", "list"]:
                return {"worktrees": [worktree("main")]}
            return {}

        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(MODULE, "run_orca", side_effect=fake_run_orca) as run:
            with patch.object(sys, "argv", ["orca-name-primaries"]):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    status = MODULE.main()

        self.assertEqual(status, 1)
        self.assertIn("down: not connected", stderr.getvalue())
        self.assertIn("up: renamed 'main' -> 'tacticalvote'", stdout.getvalue())
        self.assertIn(
            (["worktree", "set", "--worktree", "id:r1::/src/main",
              "--display-name", "tacticalvote", "--environment", "up"],),
            [c.args for c in run.call_args_list],
        )


if __name__ == "__main__":
    unittest.main()
