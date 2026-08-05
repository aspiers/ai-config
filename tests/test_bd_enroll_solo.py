#!/usr/bin/env python3
"""
Test suite for the bd-enroll-solo script.

The central guarantee of the --local profile is that enrolling a repository
into beads-solo is completely invisible to Git: a repository you do not own
must show no trace of private task tracking in branches, diffs, or PRs.

These tests assert that invariant by capturing the full `git status` output
before enrollment and requiring it to be byte-for-byte identical afterwards,
along with the supporting facts (opt-in location, exclusions, and the absence
of any tracked-file modification).

Tests that need a real Beads workspace are skipped when `bd` is unavailable or
when server mode cannot be started, so the suite stays useful on machines
without a Dolt server.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BD_ENROLL_SOLO = REPO_ROOT / "bin" / "bd-enroll-solo"

# Paths the --local profile must keep out of Git entirely.
BEADS_ARTIFACTS = (".beads", ".beads-solo")


def bd_available():
    return shutil.which("bd") is not None


class BdEnrollSoloTestCase(unittest.TestCase):
    """Shared fixture: a throwaway Git repository with one commit."""

    def setUp(self):
        self.assertTrue(
            BD_ENROLL_SOLO.exists(), f"bd-enroll-solo not found at {BD_ENROLL_SOLO}"
        )
        self.test_dir = tempfile.mkdtemp(prefix="bd-enroll-solo-test-")
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.original_dir = os.getcwd()
        self.addCleanup(os.chdir, self.original_dir)
        os.chdir(self.test_dir)

        self.run_git("init")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Test User")
        Path("README.md").write_text("# test\n")
        self.run_git("add", "README.md")
        self.run_git("commit", "-m", "init")

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout

    def git_status(self):
        """Full porcelain status, including every untracked file."""
        return self.run_git("status", "--porcelain", "--untracked-files=all")

    def enroll(self, *args, check=True):
        result = subprocess.run(
            [str(BD_ENROLL_SOLO), *args], capture_output=True, text=True
        )
        if check and result.returncode != 0:
            self.fail(
                f"bd-enroll-solo {' '.join(args)} failed "
                f"({result.returncode}):\n{result.stdout}\n{result.stderr}"
            )
        return result

    def enroll_or_skip(self):
        """Enroll with --local, skipping only on genuine environment failure.

        A violated invariant must fail the suite, so the script's own
        verification errors are never treated as "unavailable". Only an
        inability to stand up the Beads workspace justifies a skip.
        """
        result = self.enroll("--local", "--yes", "--prefix", "testrepo", check=False)
        if result.returncode == 0:
            return result

        combined = result.stdout + result.stderr
        environment_failures = (
            "required command not found",
            "could not connect",
            "connection refused",
            "dolt",
        )
        verification_failures = (
            "changed 'git status'",
            "leaked",
            "is not tracked",
            "opt-in is not recorded",
            "not in server mode",
            "no-push guard",
            "beads.role",
        )

        if any(marker in combined for marker in verification_failures):
            self.fail(f"bd-enroll-solo violated its own guarantees:\n{combined}")

        if any(marker in combined.lower() for marker in environment_failures):
            self.skipTest(f"Beads workspace unavailable here:\n{result.stderr}")

        self.fail(f"bd-enroll-solo failed unexpectedly:\n{combined}")


class TestLocalEnrollmentIsInvisibleToGit(BdEnrollSoloTestCase):
    """The --local profile must leave `git status` completely unchanged."""

    def test_dry_run_changes_nothing(self):
        before = self.git_status()
        self.enroll("--local", "--dry-run", "--prefix", "testrepo")
        self.assertEqual(
            before, self.git_status(), "--dry-run must not modify the repository"
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_git_status_identical_after_enrollment(self):
        before = self.git_status()

        self.enroll_or_skip()

        self.assertEqual(
            before,
            self.git_status(),
            "--local enrollment must leave 'git status' byte-for-byte identical",
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_enrollment_is_invisible_with_preexisting_dirty_state(self):
        """A dirty working tree must be preserved exactly, not just a clean one.

        Comparing only clean repositories would hide a bug that appends to or
        reorders existing status entries.
        """
        Path("dirty.txt").write_text("untracked\n")
        Path("README.md").write_text("# test\nmodified\n")
        before = self.git_status()
        self.assertNotEqual(before, "", "fixture should produce a dirty status")

        self.enroll_or_skip()

        self.assertEqual(
            before,
            self.git_status(),
            "--local enrollment must preserve pre-existing dirty state exactly",
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_beads_artifacts_are_ignored_and_unstaged(self):
        self.enroll_or_skip()

        staged = self.run_git("diff", "--cached", "--name-only")
        self.assertEqual(staged, "", "--local enrollment must stage nothing")

        for artifact in BEADS_ARTIFACTS:
            if not Path(artifact).exists():
                continue
            check = subprocess.run(
                ["git", "check-ignore", "-q", artifact], capture_output=True
            )
            self.assertEqual(
                check.returncode, 0, f"{artifact} exists but is not ignored by Git"
            )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_opt_in_and_exclusions_live_outside_tracked_files(self):
        self.enroll_or_skip()

        opt_in = self.run_git("config", "--local", "--get", "beads.solo.local").strip()
        self.assertEqual(opt_in, "true", "local opt-in must be in --local Git config")

        exclude = Path(".git/info/exclude").read_text()
        self.assertIn(".beads/", exclude)
        self.assertIn(".beads-solo", exclude)

        # .gitignore is published; the privacy choice must not land there.
        if Path(".gitignore").exists():
            self.assertNotIn(".beads", Path(".gitignore").read_text())


class TestLocalEnrollmentGuardrails(BdEnrollSoloTestCase):
    """Refusals and preconditions that protect against silent misuse."""

    def test_requires_yes_or_dry_run(self):
        result = self.enroll("--local", check=False)
        self.assertNotEqual(result.returncode, 0, "must refuse without --yes")
        self.assertIn("--yes", result.stderr)

    def test_refuses_outside_git_repository(self):
        outside = tempfile.mkdtemp(prefix="bd-enroll-solo-nogit-")
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        result = subprocess.run(
            [str(BD_ENROLL_SOLO), "--local", "--dry-run"],
            cwd=outside,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not inside a Git repository", result.stderr)

    def test_refuses_when_already_enrolled(self):
        Path(".beads-solo").touch()
        result = self.enroll("--local", "--dry-run", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already", result.stderr.lower())

    def test_local_mode_does_not_require_tracked_agents_md(self):
        """The tracked profile needs AGENTS.md; --local must not."""
        self.assertFalse(Path("AGENTS.md").exists())
        self.enroll("--local", "--dry-run", "--prefix", "testrepo")

    def test_tracked_mode_requires_agents_md(self):
        result = self.enroll("--dry-run", "--prefix", "testrepo", check=False)
        self.assertNotEqual(
            result.returncode, 0, "tracked profile must require AGENTS.md"
        )
        self.assertIn("AGENTS.md", result.stderr)


class TestCheckMode(BdEnrollSoloTestCase):
    """--check is the skill's entire validation surface.

    The beads-solo skill must call this and read the exit status rather than
    reproducing the checks as separate commands, so its behaviour is
    deterministic instead of reconstructed per session.
    """

    def check(self):
        return subprocess.run(
            [str(BD_ENROLL_SOLO), "--check"], capture_output=True, text=True
        )

    def test_unenrolled_repository_fails_check(self):
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not enrolled", result.stderr)

    def test_check_does_not_modify_the_repository(self):
        before = self.git_status()
        self.check()
        self.assertEqual(before, self.git_status(), "--check must be read-only")

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_reports_local_profile_after_local_enrollment(self):
        self.enroll_or_skip()
        result = self.check()
        self.assertEqual(
            result.returncode, 0, f"check failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("profile: local", result.stdout)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_check_is_read_only_on_an_enrolled_repository(self):
        self.enroll_or_skip()
        before = self.git_status()
        self.check()
        self.assertEqual(before, self.git_status())

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_detects_leaked_artifacts(self):
        """A staged Beads artifact must be reported, not silently accepted."""
        self.enroll_or_skip()
        Path(".beads-solo").touch()
        self.run_git("add", "-f", ".beads-solo")

        result = self.check()
        self.assertEqual(
            result.returncode, 1, "check must reject a leaked local enrollment"
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_detects_removed_push_guard(self):
        self.enroll_or_skip()
        subprocess.run(["bd", "config", "set", "no-push", "false"], capture_output=True)

        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no-push", result.stderr)


if __name__ == "__main__":
    unittest.main()
