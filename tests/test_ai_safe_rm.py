#!/usr/bin/env python3
"""
Test suite for ai-safe-rm script.

Tests the git-aware file deletion behavior including:
- Unmodified tracked files
- Modified tracked files
- Untracked files
- Recursive directory deletion
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
import hashlib


class TestAiSafeRm(unittest.TestCase):
    """Test cases for ai-safe-rm script."""

    def setUp(self):
        """Create a temporary git repository for testing."""
        self.test_dir = tempfile.mkdtemp(prefix="ai-safe-rm-test-")
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repo
        self.run_git("init")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Test User")

        # Get path to ai-safe-rm script
        repo_root = Path(__file__).parent.parent
        self.ai_safe_rm = repo_root / "bin" / "ai-safe-rm"
        self.assertTrue(
            self.ai_safe_rm.exists(), f"ai-safe-rm not found at {self.ai_safe_rm}"
        )

    def tearDown(self):
        """Clean up temporary test directory."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def run_git(self, *args):
        """Run a git command in the test directory."""
        result = subprocess.run(
            ["git"] + list(args), capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Git command failed: {' '.join(args)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        return result

    def run_safe_rm(self, *args, expect_success=True):
        """Run ai-safe-rm with given arguments."""
        result = subprocess.run(
            [str(self.ai_safe_rm)] + list(args),
            capture_output=True,
            text=True,
            check=False,
        )
        if expect_success and result.returncode != 0:
            raise RuntimeError(
                f"ai-safe-rm failed: {' '.join(args)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        return result

    def create_file(self, path, content="test content"):
        """Create a file with given content."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    def add_to_git(self, *paths, commit_msg):
        """Add files to git and commit them.

        Args:
            *paths: One or more file/directory paths to add
            commit_msg: Commit message
        """
        self.run_git("add", *paths)
        self.run_git("commit", "-m", commit_msg)

    def get_md5_prefix(self, content):
        """Get first 8 chars of MD5 hash of content."""
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def assert_backup_exists(self, expected_content, filename, subdir=""):
        """
        Assert that a backup file exists with correct content and hash.

        Args:
            expected_content: The content we expect in the backup
            filename: Base filename (e.g., "test.txt")
            subdir: Optional subdirectory path under .safe-rm (e.g., "dir/subdir")
        """
        hash_prefix = self.get_md5_prefix(expected_content)

        if "." in filename:
            parts = filename.rsplit(".", 1)
            base = parts[0]
            ext = parts[1]
            backup_name = f"{base}.{hash_prefix}.{ext}"
        else:
            backup_name = f"{filename}.{hash_prefix}"

        if subdir:
            backup_path = Path(f".safe-rm/{subdir}/{backup_name}")
        else:
            backup_path = Path(f".safe-rm/{backup_name}")

        self.assertTrue(backup_path.exists(), f"Backup file not found: {backup_path}")

        # Verify content matches
        actual_content = backup_path.read_text()
        self.assertEqual(
            actual_content,
            expected_content,
            f"Backup content mismatch for {backup_path}",
        )

        # Verify hash in filename matches content
        self.assertEqual(
            self.get_md5_prefix(actual_content),
            hash_prefix,
            f"MD5 hash in filename does not match file content for {backup_path}",
        )

    def assert_backup_not_exists(self, expected_content, filename, subdir=""):
        """Assert that a backup file does not exist."""
        hash_prefix = self.get_md5_prefix(expected_content)

        if "." in filename:
            parts = filename.rsplit(".", 1)
            base = parts[0]
            ext = parts[1]
            backup_name = f"{base}.{hash_prefix}.{ext}"
        else:
            backup_name = f"{filename}.{hash_prefix}"

        if subdir:
            backup_path = Path(f".safe-rm/{subdir}/{backup_name}")
        else:
            backup_path = Path(f".safe-rm/{backup_name}")

        self.assertFalse(
            backup_path.exists(), f"Backup file should not exist: {backup_path}"
        )

    def test_unmodified_tracked_file_deleted(self):
        """Unmodified tracked files should be deleted directly."""
        self.create_file("test.txt", "original")
        self.add_to_git("test.txt", commit_msg="Add test.txt")

        self.run_safe_rm("test.txt")

        self.assertFalse(Path("test.txt").exists())
        self.assertFalse(Path(".safe-rm").exists())

    def test_modified_tracked_file_backed_up(self):
        """Modified tracked files should be moved to .safe-rm with hash."""
        self.create_file("test.txt", "original")
        self.add_to_git("test.txt", commit_msg="Add test.txt")

        self.create_file("test.txt", "modified")
        self.run_safe_rm("test.txt")

        self.assertFalse(Path("test.txt").exists())
        self.assert_backup_exists("modified", "test.txt")

    def test_untracked_file_backed_up(self):
        """Untracked files should be moved to .safe-rm with hash."""
        self.create_file("untracked.txt", "untracked content")

        self.run_safe_rm("untracked.txt")

        self.assertFalse(Path("untracked.txt").exists())
        self.assert_backup_exists("untracked content", "untracked.txt")

    def test_multiple_files_mixed(self):
        """Test deleting multiple files with different statuses."""
        # Unmodified tracked
        self.create_file("unmod.txt", "unmod")
        self.add_to_git("unmod.txt", commit_msg="Add unmod")

        # Modified tracked
        self.create_file("mod.txt", "original")
        self.add_to_git("mod.txt", commit_msg="Add mod")
        self.create_file("mod.txt", "modified")

        # Untracked
        self.create_file("untracked.txt", "untracked")

        self.run_safe_rm("unmod.txt", "mod.txt", "untracked.txt")

        self.assertFalse(Path("unmod.txt").exists())
        self.assertFalse(Path("mod.txt").exists())
        self.assertFalse(Path("untracked.txt").exists())

        # Only modified and untracked should be backed up
        self.assert_backup_not_exists("unmod", "unmod.txt")
        self.assert_backup_exists("modified", "mod.txt")
        self.assert_backup_exists("untracked", "untracked.txt")

    def test_subdirectory_files_preserve_path(self):
        """Files in subdirectories should preserve their path in .safe-rm."""
        self.create_file("sub/dir/file.txt", "content")

        self.run_safe_rm("sub/dir/file.txt")

        self.assert_backup_exists("content", "file.txt", subdir="sub/dir")

    def test_directory_without_r_flag_fails(self):
        """Attempting to delete directory without -r should fail."""
        self.create_file("dir/file.txt", "content")

        result = self.run_safe_rm("dir", expect_success=False)

        self.assertEqual(result.returncode, 1)
        self.assertIn("use -r", result.stderr)
        self.assertTrue(Path("dir/file.txt").exists())

    def test_directory_all_unmodified_tracked_deleted(self):
        """Directory with only unmodified tracked files should be rm -rf'd."""
        self.create_file("dir/file1.txt", "content1")
        self.create_file("dir/file2.txt", "content2")
        self.add_to_git("dir/", commit_msg="Add dir")

        self.run_safe_rm("-r", "dir")

        self.assertFalse(Path("dir").exists())
        self.assertFalse(Path(".safe-rm").exists())

    def test_directory_with_modified_file_recurses(self):
        """Directory with modified file should recurse and backup only modified."""
        self.create_file("dir/unmod.txt", "unmod")
        self.create_file("dir/mod.txt", "original")
        self.add_to_git("dir/", commit_msg="Add dir")

        self.create_file("dir/mod.txt", "modified")

        self.run_safe_rm("-r", "dir")

        self.assertFalse(Path("dir").exists())

        # Only modified file should be backed up
        self.assert_backup_not_exists("unmod", "unmod.txt", subdir="dir")
        self.assert_backup_exists("modified", "mod.txt", subdir="dir")

    def test_directory_with_untracked_file_recurses(self):
        """Directory with untracked file should recurse and backup untracked."""
        self.create_file("dir/tracked.txt", "tracked")
        self.add_to_git("dir/", commit_msg="Add dir")

        self.create_file("dir/untracked.txt", "untracked")

        self.run_safe_rm("-r", "dir")

        self.assertFalse(Path("dir").exists())

        # Only untracked file should be backed up
        self.assert_backup_not_exists("tracked", "tracked.txt", subdir="dir")
        self.assert_backup_exists("untracked", "untracked.txt", subdir="dir")

    def test_nested_directory_structure(self):
        """Test recursive deletion with nested directories."""
        self.create_file("parent/child1/file1.txt", "unmod1")
        self.create_file("parent/child2/file2.txt", "original")
        self.add_to_git("parent/", commit_msg="Add parent")

        # Modify a tracked file
        self.create_file("parent/child2/file2.txt", "modified_content")
        # Add an untracked file
        self.create_file("parent/child2/untracked.txt", "untracked_content")

        self.run_safe_rm("-r", "parent")

        self.assertFalse(Path("parent").exists())

        # Unmodified tracked files should NOT be backed up
        self.assert_backup_not_exists("unmod1", "file1.txt", subdir="parent/child1")
        self.assert_backup_not_exists("original", "file2.txt", subdir="parent/child2")

        # Only modified and untracked should be backed up
        self.assert_backup_exists(
            "modified_content", "file2.txt", subdir="parent/child2"
        )
        self.assert_backup_exists(
            "untracked_content", "untracked.txt", subdir="parent/child2"
        )

    def test_nonexistent_file_warning(self):
        """Deleting nonexistent file should warn but not fail."""
        result = self.run_safe_rm("nonexistent.txt")

        self.assertIn("does not exist", result.stderr)
        self.assertEqual(result.returncode, 0)

    def test_not_in_git_repo_fails(self):
        """Running outside git repo should fail."""
        os.chdir(self.original_dir)
        temp_dir = tempfile.mkdtemp(prefix="no-git-")
        try:
            os.chdir(temp_dir)
            Path("test.txt").write_text("content")

            result = self.run_safe_rm("test.txt", expect_success=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Not in a git repository", result.stderr)
        finally:
            os.chdir(self.original_dir)
            shutil.rmtree(temp_dir)

    def test_hash_collision_handling(self):
        """Multiple versions of same file should create unique backups."""
        self.create_file("file.txt", "version1")
        self.run_safe_rm("file.txt")

        self.create_file("file.txt", "version2")
        self.run_safe_rm("file.txt")

        # Verify both backups exist with different hashes
        self.assert_backup_exists("version1", "file.txt")
        self.assert_backup_exists("version2", "file.txt")

    def test_empty_directory_cleanup(self):
        """Empty directories should be removed after recursive processing."""
        self.create_file("dir/subdir/file.txt", "content")
        self.add_to_git("dir/", commit_msg="Add dir")

        self.run_safe_rm("-r", "dir")

        self.assertFalse(Path("dir").exists())
        self.assertFalse(Path("dir/subdir").exists())

    def test_file_outside_repo_fails(self):
        """Deleting files outside the repo should fail and NOT delete the file."""
        outside_dir = tempfile.mkdtemp(prefix="outside-")
        try:
            Path(outside_dir, "outside.txt").write_text("outside content")

            result = self.run_safe_rm(
                f"{outside_dir}/outside.txt", expect_success=False
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("outside the git repository", result.stderr)
            self.assertTrue(
                Path(outside_dir, "outside.txt").exists(),
                "File outside repo was deleted!",
            )
        finally:
            shutil.rmtree(outside_dir)


if __name__ == "__main__":
    unittest.main()
