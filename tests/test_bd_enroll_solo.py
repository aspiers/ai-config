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
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BD_ENROLL_SOLO = REPO_ROOT / "bin" / "bd-enroll-solo"
PRIME_TEMPLATE = REPO_ROOT / ".agents" / "skills" / "beads-solo" / "assets" / "PRIME.md"

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

    def enroll_or_skip(self, local=True):
        """Enroll (--local by default), skipping only on environment failure.

        A violated invariant must fail the suite, so the script's own
        verification errors are never treated as "unavailable". Only an
        inability to stand up the Beads workspace justifies a skip.
        """
        profile_args = ("--local",) if local else ()
        result = self.enroll(
            *profile_args, "--yes", "--prefix", "testrepo", check=False
        )
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
            "beads.role is not pinned",
            "diverged",
            "Dolt remote 'origin' is still configured",
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


class TestBeadsStateStaysLocal(BdEnrollSoloTestCase):
    """'bd init' wires git origin as a Dolt remote; enrollment must undo it."""

    def add_git_origin(self):
        origin = Path(tempfile.mkdtemp(prefix="bd-enroll-origin-test-"))
        self.addCleanup(shutil.rmtree, origin, ignore_errors=True)
        subprocess.run(
            ["git", "init", "--bare", str(origin)], capture_output=True, check=True
        )
        self.run_git("remote", "add", "origin", str(origin))

    def dolt_remotes(self):
        return subprocess.run(
            ["bd", "dolt", "remote", "list"],
            capture_output=True,
            text=True,
            env=self.command_env,
            check=True,
        ).stdout

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_no_dolt_remote_after_enrollment_with_git_origin(self):
        self.add_git_origin()

        self.enroll_or_skip()

        self.assertIn("No remotes configured", self.dolt_remotes())
        config = Path(".beads/config.yaml").read_text()
        self.assertNotRegex(config, r"(?m)^\s*sync\.remote:")

    def test_dry_run_plans_the_remote_removal(self):
        result = self.enroll("--local", "--dry-run", "--prefix", "testrepo")
        self.assertIn("bd dolt remote remove origin", result.stdout)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_check_and_repair_remote_on_a_real_workspace(self):
        """An enrollment predating remote removal must fail --check and be
        repairable, as a workspace enrolled before d53bb45 would be."""
        self.enroll_or_skip()
        origin = Path(tempfile.mkdtemp(prefix="bd-enroll-dolt-origin-test-"))
        self.addCleanup(shutil.rmtree, origin, ignore_errors=True)
        added = subprocess.run(
            ["bd", "dolt", "remote", "add", "origin", f"file://{origin}"],
            capture_output=True,
            text=True,
            env=self.command_env,
        )
        if added.returncode != 0:
            self.skipTest(f"cannot add a Dolt remote here:\n{added.stderr}")

        result = self.enroll("--check", check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(str(origin), result.stderr)
        self.assertIn("--repair-remote", result.stderr)

        self.enroll("--repair-remote", "--yes")

        self.assertIn("No remotes configured", self.dolt_remotes())
        config = Path(".beads/config.yaml").read_text()
        self.assertNotRegex(config, r"(?m)^\s*sync\.remote:")
        result = self.enroll("--check", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


# Stands in for bd so the migration gate, which cannot be provoked on demand
# with a real workspace, can be tested. It records every call, and answers
# the way bd 1.3.0 does on a gated remote-backed database when 'gated' exists
# in its state directory: 'bd dolt remote list' works, everything that opens
# the database is refused.
FAKE_BD = """#!/bin/sh
state=$FAKE_BD_STATE
echo "$*" >>"$state/calls"
refusal="refusing to auto-apply 3 pending schema migrations to a \
remote-backed database (v12 -> v15): migrating clones independently \
forks the schema (#4259)"
case "$*" in
    "dolt remote list")
        if [ -f "$state/remote" ]; then
            printf 'origin               %s\\n' "$(cat "$state/remote")"
        else
            echo "No remotes configured."
        fi ;;
    "dolt remote remove origin")
        if [ -f "$state/gated" ]; then
            echo "Error removing remote: $refusal" >&2
            exit 1
        fi
        rm -f "$state/remote" ;;
    "context --json")
        [ -f "$state/gated" ] && { echo "Error: $refusal" >&2; exit 1; }
        echo '{"dolt_mode": "server"}' ;;
    "config get export.git-add")
        [ -f "$state/gated" ] && { echo "Error: $refusal" >&2; exit 1; }
        echo "export.git-add = false" ;;
    "memories --json")
        echo '[{"key": "beads-solo-policy"}]' ;;
    *)
        exit 1 ;;
esac
"""

UPSTREAM_URL = "git+ssh://git@example.com/upstream/project.git"


class FakeBdEnrollmentTestCase(BdEnrollSoloTestCase):
    """A local enrollment backed by FAKE_BD instead of a Dolt server."""

    def setUp(self):
        super().setUp()
        self.state = Path(self.test_dir, "fake-bd-state")
        self.state.mkdir()
        fake_bin = Path(self.test_dir, "fake-bin")
        fake_bin.mkdir()
        (fake_bin / "bd").write_text(FAKE_BD)
        (fake_bin / "bd").chmod(0o755)

        home = Path(self.test_dir, "home")
        (home / ".agents" / "skills").mkdir(parents=True)
        (home / ".agents" / "skills" / "beads").symlink_to(self.skill_source)

        self.command_env.update(
            FAKE_BD_STATE=str(self.state),
            HOME=str(home),
            PATH=f"{fake_bin}{os.pathsep}{self.command_env['PATH']}",
        )

        self.run_git("config", "--local", "beads.solo.local", "true")
        self.run_git("config", "--local", "beads.role", "maintainer")
        with Path(".git/info/exclude").open("a") as exclude:
            exclude.write(".beads/\n.beads-solo\nfake-bd-state/\n")
            exclude.write("fake-bin/\nhome/\n")
        Path(".beads").mkdir()
        self.config = Path(".beads/config.yaml")
        self.config.write_text("issue-prefix: testrepo\n")

    def bd_calls(self):
        calls = self.state / "calls"
        return calls.read_text().splitlines() if calls.exists() else []


class TestRemoteRepair(FakeBdEnrollmentTestCase):
    """--check and --repair-remote on an enrollment that kept its remote."""

    def setUp(self):
        super().setUp()
        # A local enrollment as bd-enroll-solo made it before d53bb45.
        (self.state / "remote").write_text(UPSTREAM_URL)
        self.config.write_text(
            "issue-prefix: testrepo\n" f'sync.remote: "{UPSTREAM_URL}"\n'
        )

    def gate_migrations(self):
        (self.state / "gated").touch()

    def assert_never_pushed_or_migrated(self):
        forbidden = re.compile(r"\b(push|migrate|bootstrap)\b|^(export|dolt commit)")
        for call in self.bd_calls():
            self.assertNotRegex(call, forbidden)

    def test_check_reports_remote_even_when_database_is_gated(self):
        self.gate_migrations()

        result = self.enroll("--check", check=False)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            f"a Dolt remote 'origin' is still configured ({UPSTREAM_URL})",
            result.stderr,
        )
        self.assertIn(
            f'sync.remote is still set in .beads/config.yaml ("{UPSTREAM_URL}")',
            result.stderr,
        )
        self.assertIn("bd-enroll-solo --repair-remote --yes", result.stderr)
        self.assertNotIn("could not be validated", result.stderr)

    def test_check_accepts_a_commented_out_sync_remote(self):
        (self.state / "remote").unlink()
        self.config.write_text(f'# sync.remote: "{UPSTREAM_URL}"\n')

        result = self.enroll("--check", check=False)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repair_remote_removes_remote_and_disables_sync_remote(self):
        result = self.enroll("--repair-remote", "--yes")

        self.assertIn("dolt remote remove origin", self.bd_calls())
        self.assertFalse((self.state / "remote").exists())
        config = self.config.read_text()
        self.assertNotRegex(config, r"(?m)^\s*sync\.remote:")
        self.assertIn(f'# sync.remote: "{UPSTREAM_URL}"', config)
        self.assertIn("profile: local", result.stdout)
        self.assert_never_pushed_or_migrated()

    def test_repair_remote_explains_the_migration_gate(self):
        self.gate_migrations()

        result = self.enroll("--repair-remote", "--yes", check=False)

        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing to auto-apply", result.stderr)
        self.assertIn("schema migrations are pending", result.stderr)
        self.assertIn(UPSTREAM_URL, result.stderr)
        steps = [
            "bd export --all -o .beads/backup/pre-migrate-",
            "bd dolt commit",
            "bd migrate --force",
            "bd dolt remote remove origin",
        ]
        positions = [result.stderr.find(step) for step in steps]
        self.assertNotIn(-1, positions, result.stderr)
        self.assertEqual(positions, sorted(positions), "steps out of order")
        self.assertIn("Do NOT run 'bd dolt push' or 'bd bootstrap'", result.stderr)
        self.assert_never_pushed_or_migrated()
        self.assertTrue((self.state / "remote").exists())

    def test_repair_remote_dry_run_changes_nothing(self):
        before = self.config.read_text()

        result = self.enroll("--repair-remote", "--dry-run")

        self.assertIn("bd dolt remote remove origin", result.stdout)
        self.assertEqual(before, self.config.read_text())
        self.assertNotIn("dolt remote remove origin", self.bd_calls())

    def test_repair_remote_requires_yes(self):
        result = self.enroll("--repair-remote", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--yes", result.stderr)
        self.assertTrue((self.state / "remote").exists())

    def test_repair_remote_cannot_be_combined_with_check(self):
        result = self.enroll("--repair-remote", "--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be combined", result.stderr)


class TestPrimeTemplate(FakeBdEnrollmentTestCase):
    """.beads/PRIME.md replaces bd prime's default text with the beads-solo one.

    Missing or stale files are warnings, never failures: enrollments made
    before the template existed must keep passing --check.
    """

    prime = Path(".beads/PRIME.md")

    def make_tracked(self, declaration):
        self.run_git("config", "--local", "--unset", "beads.solo.local")
        exclude = Path(".git/info/exclude")
        exclude.write_text(
            "".join(
                line
                for line in exclude.read_text().splitlines(keepends=True)
                if line.strip() not in (".beads/", ".beads-solo")
            )
        )
        self.run_git("add", ".beads/config.yaml")
        Path(".beads-solo").touch()
        Path("AGENTS.md").write_text(f"# AGENTS.md\n\n{declaration}\n")
        self.run_git("add", "-f", ".beads-solo", "AGENTS.md")
        self.run_git("commit", "-m", "tracked enrollment")

    def test_template_tells_agents_to_load_all_three_skills(self):
        template = PRIME_TEMPLATE.read_text()
        for skill in ("`beads-solo`", "`beads`", "`beads-best-practices`"):
            self.assertIn(skill, template)
        self.assertIn("reads included", template)
        self.assertIn("bd comments add", template)
        self.assertNotRegex(template, r"bd (create|update)[^\n]*--notes")
        self.assertNotRegex(template, r"(?m)^git push")

    def test_check_warns_but_passes_when_prime_is_missing(self):
        result = self.enroll("--check", check=False)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("profile: local", result.stdout)
        self.assertIn(".beads/PRIME.md is missing", result.stderr)
        self.assertIn("bd-enroll-solo --repair-prime --yes", result.stderr)

    def test_check_warns_when_prime_differs_from_template(self):
        self.prime.write_text("custom\n")

        result = self.enroll("--check", check=False)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("differs from the beads-solo template", result.stderr)

    def test_repair_prime_installs_template_invisibly_in_local_profile(self):
        before = self.git_status()

        result = self.enroll("--repair-prime", "--yes")

        self.assertEqual(self.prime.read_text(), PRIME_TEMPLATE.read_text())
        self.assertEqual(before, self.git_status())
        self.assertIn("profile: local", result.stdout)
        self.assertNotIn("PRIME.md", result.stderr)

    def test_repair_prime_stages_file_in_tracked_profile(self):
        self.make_tracked(
            "Before running any `bd` command, load the `beads-solo` (policy)"
        )

        result = self.enroll("--repair-prime", "--yes")

        self.assertIn("profile: tracked", result.stdout)
        self.assertEqual(
            self.run_git("diff", "--cached", "--name-only").split(),
            [".beads/PRIME.md"],
        )
        self.assertNotIn("PRIME.md", result.stderr)
        self.assertNotIn("warnings", result.stderr)

    def test_check_warns_about_legacy_agents_md_declaration(self):
        self.make_tracked("Use the `beads-solo` skill for Beads setup.")
        self.enroll("--repair-prime", "--yes")

        result = self.enroll("--check", check=False)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("old beads-solo declaration", result.stderr)
        self.assertIn("`beads-best-practices`", result.stderr)

    def test_repair_prime_dry_run_changes_nothing(self):
        result = self.enroll("--repair-prime", "--dry-run")

        self.assertIn(".beads/PRIME.md", result.stdout)
        self.assertFalse(self.prime.exists())

    def test_repair_prime_requires_yes(self):
        result = self.enroll("--repair-prime", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--yes", result.stderr)
        self.assertFalse(self.prime.exists())

    def test_template_override_and_missing_template(self):
        custom = Path(self.test_dir, "home", "PRIME.md")
        custom.write_text("override\n")
        env = dict(self.command_env, BEADS_SOLO_PRIME_TEMPLATE=str(custom))
        self.enroll("--repair-prime", "--yes", env=env)
        self.assertEqual(self.prime.read_text(), "override\n")

        env["BEADS_SOLO_PRIME_TEMPLATE"] = str(custom.with_name("missing.md"))
        result = self.enroll("--repair-prime", "--yes", check=False, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("template not found", result.stderr)

    def test_enrollment_dry_run_plans_prime_install(self):
        self.run_git("config", "--local", "--unset", "beads.solo.local")
        shutil.rmtree(".beads")

        result = self.enroll("--local", "--dry-run", "--prefix", "testrepo")

        self.assertRegex(result.stdout, r"Installing \S*\.beads/PRIME\.md")
        self.assertFalse(self.prime.exists())


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
        self.assertNotIn("warnings", result.stderr)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_bd_prime_uses_the_installed_template(self):
        self.enroll_or_skip()
        self.assertEqual(
            Path(".beads/PRIME.md").read_text(), PRIME_TEMPLATE.read_text()
        )

        prime = subprocess.run(
            ["bd", "prime"],
            capture_output=True,
            text=True,
            env=self.command_env,
            check=True,
        ).stdout

        self.assertIn("## Before Any bd Command", prime)
        self.assertIn("`beads-best-practices`", prime)

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_reports_tracked_profile_after_tracked_enrollment(self):
        """A fresh tracked enrollment must pass --check immediately.

        Without a CLAUDE.md, 'bd init' used to create a regular one from its
        own template, diverging it from AGENTS.md so that --check failed
        straight after a successful enrollment.
        """
        Path("AGENTS.md").write_text("# AGENTS.md\n\nHello.\n")
        self.run_git("add", "AGENTS.md")
        self.run_git("commit", "-m", "add AGENTS.md")

        self.enroll_or_skip(local=False)
        result = self.check()
        self.assertEqual(
            result.returncode, 0, f"check failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("profile: tracked", result.stdout)
        self.assertNotIn("warnings", result.stderr)
        self.assertIn(
            ".beads/PRIME.md", self.run_git("diff", "--cached", "--name-only")
        )
        self.assertIn("`beads-best-practices`", Path("AGENTS.md").read_text())
        self.assertTrue(
            Path("CLAUDE.md").is_symlink(), "CLAUDE.md should symlink to AGENTS.md"
        )
        self.assertEqual(os.readlink("CLAUDE.md"), "AGENTS.md")
        self.assertIn(
            "false",
            subprocess.run(
                ["bd", "config", "get", "export.git-add"],
                capture_output=True,
                text=True,
                env=self.command_env,
            ).stdout,
        )

    @unittest.skipUnless(bd_available(), "bd not installed")
    def test_unreachable_database_is_not_reported_as_wrong_settings(self):
        """A bd failure must not masquerade as a policy violation.

        'bd config get' exits 1 whenever the Dolt server is unreachable, even
        for keys stored in config.yaml. Agents reading "export.git-add is not
        false" then ran a pointless repair; the check must name the cause.
        """
        self.enroll_or_skip()
        env = dict(self.command_env, BEADS_DOLT_SERVER_HOST="10.255.255.1")
        result = subprocess.run(
            [str(BD_ENROLL_SOLO), "--check"],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("could not be validated", result.stderr)
        self.assertIn("sandboxed", result.stderr)
        self.assertIn("Do NOT run 'bd config set'", result.stderr)
        self.assertNotIn("enrollment is malformed", result.stderr)
        self.assertNotIn("export.git-add is not false", result.stderr)
        self.assertNotIn("policy memory", result.stderr)

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
