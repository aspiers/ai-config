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
BEADS_ARTIFACTS = (
    ".beads",
    ".beads-solo",
    ".agents/skills/beads",
    ".claude/skills/beads",
)
BEADS_SKILL_LINKS = (".agents/skills/beads", ".claude/skills/beads")


def bd_available():
    return shutil.which("bd") is not None


class BdEnrollSoloTestCase(unittest.TestCase):
    """Shared fixture: a throwaway Git repository with one commit."""

    def setUp(self):
        self.assertTrue(
            BD_ENROLL_SOLO.exists(), f"bd-enroll-solo not found at {BD_ENROLL_SOLO}"
        )
        self.test_dir = tempfile.mkdtemp(prefix="bd-enroll-solo-test-")
        self.addCleanup(self.cleanup_test_dir)
        self.original_dir = os.getcwd()
        self.addCleanup(os.chdir, self.original_dir)
        os.chdir(self.test_dir)

        self.skill_source = Path(tempfile.mkdtemp(prefix="beads-skill-test-"))
        self.addCleanup(shutil.rmtree, self.skill_source, ignore_errors=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: beads\ndescription: Test Beads skill\n---\n"
        )
        self.command_env = os.environ.copy()
        self.command_env["BEADS_SKILL_DIR"] = str(self.skill_source)

        self.run_git("init")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Test User")
        Path("README.md").write_text("# test\n")
        self.run_git("add", "README.md")
        self.run_git("commit", "-m", "init")

    def cleanup_test_dir(self):
        """Stop the fixture's server, then remove its temporary repository."""
        self.stop_dolt_server()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def stop_dolt_server(self):
        """Stop a server created for this fixture before deleting its files."""
        pid_file = Path(self.test_dir, ".beads", "dolt-server.pid")
        if not pid_file.exists():
            return

        pid = int(pid_file.read_text().strip())
        result = subprocess.run(
            ["bd", "-C", self.test_dir, "dolt", "stop"],
            capture_output=True,
            text=True,
            env=self.command_env,
            timeout=30,
        )
        if result.returncode != 0:
            self.fail(
                "failed to stop the test Dolt server "
                f"({result.returncode}):\n{result.stdout}\n{result.stderr}"
            )

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        self.fail(f"test Dolt server PID {pid} survived 'bd dolt stop'")

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout

    def git_status(self):
        """Full porcelain status, including every untracked file."""
        return self.run_git("status", "--porcelain", "--untracked-files=all")

    def enroll(self, *args, check=True, env=None):
        result = subprocess.run(
            [str(BD_ENROLL_SOLO), *args],
            capture_output=True,
            text=True,
            env=env or self.command_env,
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
        for link in BEADS_SKILL_LINKS:
            self.assertIn(link, exclude)

        # .gitignore is published; the privacy choice must not land there.
        if Path(".gitignore").exists():
            self.assertNotIn(".beads", Path(".gitignore").read_text())

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_installs_repository_local_skill_symlinks(self):
        self.enroll_or_skip()

        for link in BEADS_SKILL_LINKS:
            path = Path(link)
            self.assertTrue(path.is_symlink(), f"{link} should be a symlink")
            self.assertEqual(path.resolve(), self.skill_source.resolve())

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_local_enrollment_works_in_a_linked_worktree(self):
        worktree = Path(tempfile.mkdtemp(prefix="bd-enroll-worktree-test-"))
        shutil.rmtree(worktree)
        self.run_git("worktree", "add", "-b", "enrollment-test", str(worktree))
        try:
            os.chdir(worktree)
            self.enroll_or_skip()
            exclude_path = Path(
                self.run_git("rev-parse", "--git-path", "info/exclude").strip()
            )
            if not exclude_path.is_absolute():
                exclude_path = worktree / exclude_path
            exclude = exclude_path.read_text()
            for link in BEADS_SKILL_LINKS:
                self.assertIn(link, exclude)
        finally:
            os.chdir(self.test_dir)
            self.run_git("worktree", "remove", "--force", str(worktree))


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

    def test_dry_run_preserves_existing_valid_skill_installations(self):
        for link in BEADS_SKILL_LINKS:
            path = Path(link)
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                "---\nname: beads\ndescription: Existing skill\n---\n"
            )
            self.run_git("add", link)
        self.run_git("commit", "-m", "add existing skills")

        self.enroll("--local", "--dry-run", "--prefix", "testrepo")

        for link in BEADS_SKILL_LINKS:
            self.assertTrue(Path(link).is_dir())
            self.assertFalse(Path(link).is_symlink())

    def test_local_enrollment_refuses_visible_existing_skill_before_mutation(self):
        path = Path(BEADS_SKILL_LINKS[0])
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(
            "---\nname: beads\ndescription: Untracked skill\n---\n"
        )

        result = self.enroll(
            "--local", "--dry-run", "--prefix", "testrepo", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists and is visible to Git", result.stderr)
        opt_in = subprocess.run(
            ["git", "config", "--local", "--get", "beads.solo.local"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(opt_in.returncode, 0)

    def test_refuses_higher_precedence_skill_negation_before_enrollment(self):
        Path(".gitignore").write_text("!.agents/skills/beads\n")
        self.run_git("add", ".gitignore")
        self.run_git("commit", "-m", "add skill negation")
        exclude = Path(".git/info/exclude")
        exclude_before = exclude.read_text()

        for confirmation in ("--dry-run", "--yes"):
            result = self.enroll(
                "--local", confirmation, "--prefix", "testrepo", check=False
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("higher-precedence negation", result.stderr)
            self.assertEqual(exclude.read_text(), exclude_before)
            self.assertFalse(Path(BEADS_SKILL_LINKS[0]).exists())
            opt_in = subprocess.run(
                ["git", "config", "--local", "--get", "beads.solo.local"],
                capture_output=True,
            )
            self.assertNotEqual(opt_in.returncode, 0)
            self.assertFalse(Path(".beads").exists())

    def test_auto_detects_skill_in_packaged_share_directory(self):
        prefix = Path(tempfile.mkdtemp(prefix="beads-install-test-"))
        self.addCleanup(shutil.rmtree, prefix, ignore_errors=True)
        fake_bd = prefix / "bin" / "bd"
        fake_bd.parent.mkdir()
        fake_bd.write_text("#!/bin/sh\nexit 0\n")
        fake_bd.chmod(0o755)
        skill = prefix / "share" / "beads" / "skills" / "beads"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: beads\ndescription: Packaged skill\n---\n"
        )
        env = self.command_env.copy()
        env.pop("BEADS_SKILL_DIR")
        env["PATH"] = f"{fake_bd.parent}{os.pathsep}{env['PATH']}"

        result = self.enroll(
            "--local", "--dry-run", "--prefix", "testrepo", env=env
        )

        self.assertIn(f"Beads skill: {skill}", result.stdout)

    def test_reports_when_skill_source_cannot_be_detected(self):
        prefix = Path(tempfile.mkdtemp(prefix="empty-beads-install-test-"))
        self.addCleanup(shutil.rmtree, prefix, ignore_errors=True)
        fake_bd = prefix / "bin" / "bd"
        fake_bd.parent.mkdir()
        fake_bd.write_text("#!/bin/sh\nexit 0\n")
        fake_bd.chmod(0o755)
        env = self.command_env.copy()
        env.pop("BEADS_SKILL_DIR")
        env["HOME"] = str(prefix / "home")
        env["XDG_DATA_HOME"] = str(prefix / "data")
        env["PATH"] = f"{fake_bd.parent}{os.pathsep}{env['PATH']}"

        result = self.enroll(
            "--local",
            "--dry-run",
            "--prefix",
            "testrepo",
            check=False,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not locate the Beads skill", result.stderr)
        self.assertIn("BEADS_SKILL_DIR", result.stderr)


class TestCheckMode(BdEnrollSoloTestCase):
    """--check is the skill's entire validation surface.

    The beads-solo skill must call this and read the exit status rather than
    reproducing the checks as separate commands, so its behaviour is
    deterministic instead of reconstructed per session.
    """

    def check(self):
        return subprocess.run(
            [str(BD_ENROLL_SOLO), "--check"],
            capture_output=True,
            text=True,
            env=self.command_env,
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
    def test_accepts_global_skill_without_repository_links(self):
        self.enroll_or_skip()
        for link in BEADS_SKILL_LINKS:
            Path(link).unlink()

        global_skill = Path(self.test_dir, "home", ".agents", "skills", "beads")
        global_skill.parent.mkdir(parents=True)
        global_skill.symlink_to(self.skill_source)
        self.command_env["HOME"] = str(Path(self.test_dir, "home"))

        result = self.check()
        self.assertEqual(
            result.returncode, 0, f"check failed:\n{result.stdout}\n{result.stderr}"
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_rejects_enrollment_without_any_available_skill(self):
        self.enroll_or_skip()
        for link in BEADS_SKILL_LINKS:
            Path(link).unlink()
        empty_home = Path(self.test_dir, "empty-home")
        empty_home.mkdir()
        self.command_env["HOME"] = str(empty_home)

        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no valid Beads skill found", result.stderr)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_detects_missing_skill_link_exclusion(self):
        self.enroll_or_skip()
        exclude = Path(".git/info/exclude")
        excluded_link = BEADS_SKILL_LINKS[1]
        exclude.write_text(
            "\n".join(
                line for line in exclude.read_text().splitlines()
                if line != excluded_link
            )
            + "\n"
        )

        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{excluded_link} is not listed", result.stderr)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_repair_skills_restores_a_missing_link(self):
        self.enroll_or_skip()
        missing_link = Path(BEADS_SKILL_LINKS[1])
        missing_link.unlink()

        self.enroll("--repair-skills", "--yes")

        self.assertTrue(missing_link.is_symlink())
        self.assertEqual(missing_link.resolve(), self.skill_source.resolve())
        self.assertEqual(self.check().returncode, 0)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_repair_skills_replaces_a_broken_link(self):
        self.enroll_or_skip()
        broken_link = Path(BEADS_SKILL_LINKS[1])
        broken_link.unlink()
        broken_link.symlink_to(self.skill_source / "missing")

        self.enroll("--repair-skills", "--yes")

        self.assertEqual(broken_link.resolve(), self.skill_source.resolve())
        self.assertEqual(self.check().returncode, 0)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_repair_refuses_to_replace_a_tracked_broken_link(self):
        self.enroll_or_skip()
        broken_link = Path(BEADS_SKILL_LINKS[1])
        self.run_git("add", "-f", str(broken_link))
        broken_link.unlink()
        broken_target = self.skill_source / "missing"
        broken_link.symlink_to(broken_target)
        before = self.git_status()

        result = self.enroll("--repair-skills", "--yes", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid or missing tracked content", result.stderr)
        self.assertEqual(os.readlink(broken_link), str(broken_target))
        self.assertEqual(self.git_status(), before)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_detects_tracked_skill_symlink(self):
        self.enroll_or_skip()
        tracked_link = BEADS_SKILL_LINKS[1]
        self.run_git("add", "-f", tracked_link)

        result = self.check()

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{tracked_link} is a tracked absolute symlink", result.stderr)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_detects_ineffective_skill_exclusion(self):
        self.enroll_or_skip()
        link = BEADS_SKILL_LINKS[1]
        with Path(".git/info/exclude").open("a") as exclude:
            exclude.write(f"!{link}\n")

        result = self.check()

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{link} is not effectively ignored", result.stderr)

        self.enroll("--repair-skills", "--yes")
        self.assertEqual(self.check().returncode, 0)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_check_ignores_no_push_setting(self):
        self.enroll_or_skip()
        self.assertNotRegex(
            Path(".beads/config.yaml").read_text(),
            r"(?m)^no-push:",
            "enrollment must leave the optional no-push setting unset",
        )

        for action in (("set", "no-push", "false"), ("unset", "no-push")):
            subprocess.run(["bd", "config", *action], capture_output=True, check=True)
            result = self.check()
            self.assertEqual(
                result.returncode,
                0,
                f"check failed:\n{result.stdout}\n{result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
