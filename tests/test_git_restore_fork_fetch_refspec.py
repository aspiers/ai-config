#!/usr/bin/env python3
"""
Test suite for the git-restore-fork-fetch-refspec pre-push hook.

Each test pushes a branch from a scratch repository, with the script
installed as a config-based pre-push hook, and checks which fetch refspecs
the remote ends up with and whether the pushed branch's upstream resolves.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).parent.parent / "bin" / "git-restore-fork-fetch-refspec"


class TestGitRestoreForkFetchRefspec(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo = root / "repo"
        self.env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        self.bare = root / "fork.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.bare)], check=True, env=self.env)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, env=self.env)
        self.git("commit", "-q", "--allow-empty", "-m", "init")
        self.git("config", "hook.fork-fetch-refspec.event", "pre-push")
        self.git("config", "hook.fork-fetch-refspec.command", str(HOOK))
        self.git("switch", "-q", "-c", "b")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            env=self.env,
            check=check,
        )
        return result.stdout

    def add_remote(self, name: str, *fetch: str) -> None:
        self.git("remote", "add", name, str(self.bare))
        self.git("config", "--unset-all", f"remote.{name}.fetch")
        for refspec in fetch:
            self.git("config", "--add", f"remote.{name}.fetch", refspec)

    def push_and_read(self, name: str) -> tuple[list[str], str]:
        self.git("push", "-q", "-u", name, "b")
        fetch = self.git("config", "--get-all", f"remote.{name}.fetch", check=False).split()
        upstream = self.git("for-each-ref", "--format=%(upstream)", "refs/heads/b").strip()
        return fetch, upstream

    def test_widens_remote_narrowed_by_orca(self):
        narrow = "+refs/heads/a*:refs/remotes/fork/a*"
        self.add_remote("fork", narrow)
        fetch, upstream = self.push_and_read("fork")
        self.assertEqual(fetch, [narrow, "+refs/heads/*:refs/remotes/fork/*"])
        self.assertEqual(upstream, "refs/remotes/fork/b")

    def test_leaves_wide_remote_alone(self):
        wide = "+refs/heads/*:refs/remotes/fork/*"
        self.add_remote("fork", "+refs/heads/a*:refs/remotes/fork/a*", wide)
        fetch, _ = self.push_and_read("fork")
        self.assertEqual(fetch.count(wide), 1)

    def test_leaves_orca_and_reserved_remotes_narrow(self):
        for name in ["pr-someone-repo", "origin", "upstream"]:
            with self.subTest(remote=name):
                narrow = f"+refs/heads/a*:refs/remotes/{name}/a*"
                self.add_remote(name, narrow)
                fetch, _ = self.push_and_read(name)
                self.assertEqual(fetch, [narrow])

    def test_leaves_orca_created_remote_narrow(self):
        narrow = "+refs/heads/a*:refs/remotes/fork/a*"
        self.add_remote("fork", narrow)
        self.git("config", "remote.fork.orca-created", "true")
        fetch, _ = self.push_and_read("fork")
        self.assertEqual(fetch, [narrow])

    def test_leaves_other_custom_refspecs_alone(self):
        # e.g. a remote set up to follow one colleague's branch exactly.
        literal = "+refs/heads/a:refs/remotes/fork/a"
        self.add_remote("fork", literal)
        fetch, _ = self.push_and_read("fork")
        self.assertEqual(fetch, [literal])

    def test_push_to_bare_url_succeeds(self):
        self.git("push", "-q", str(self.bare), "b")


if __name__ == "__main__":
    unittest.main()
