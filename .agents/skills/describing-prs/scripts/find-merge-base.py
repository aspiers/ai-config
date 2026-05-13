#!/usr/bin/env python3
"""Find the base branch for the current branch.

Determines the best base branch by finding the most recent ancestor
that exists on a remote branch. This handles cases where you branched
from a feature branch, not just main/master.

Output: The base branch name (or error message to stderr with exit 1)
"""

import argparse
import subprocess
import sys

DEBUG = False

# Remotes to consider, in priority order
PREFERRED_REMOTES = ["origin", "upstream", "github"]

# Branch names that are typically "main" branches (not feature branches)
DEFAULT_BRANCH_NAMES = ["develop", "dev", "main", "master"]


def debug(msg: str) -> None:
    """Print debug message to stderr if debug mode is enabled."""
    if DEBUG:
        print(f"[debug] {msg}", file=sys.stderr)


def run_git(*args: str) -> str | None:
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_remote_branches() -> list[str]:
    """Get list of remote branch refs (e.g., origin/main)."""
    output = run_git("branch", "-r", "--format=%(refname:short)")
    if not output:
        return []
    return [b.strip() for b in output.splitlines() if b.strip()]


def try_upstream() -> tuple[str | None, str | None]:
    """Try @{upstream} (the current branch's configured upstream)."""
    debug("Trying @{upstream}")
    upstream = run_git("rev-parse", "--abbrev-ref", "@{upstream}")
    if not upstream:
        debug("  no upstream configured")
        return None, None

    debug(f"  upstream is {upstream}")
    base = run_git("merge-base", "HEAD", "@{upstream}")
    if base:
        debug(f"  found merge-base {base[:12]} with {upstream}")
        return upstream, "@{upstream}"

    debug("  could not determine merge-base with upstream")
    return None, None


def try_origin_head() -> tuple[str | None, str | None]:
    """Try origin/HEAD (the remote's default branch)."""
    debug("Trying origin/HEAD")
    # Resolve origin/HEAD to actual branch name
    target = run_git("symbolic-ref", "refs/remotes/origin/HEAD")
    if not target:
        debug("  origin/HEAD not available")
        return None, None

    # Convert refs/remotes/origin/main -> origin/main
    branch = target.replace("refs/remotes/", "")
    debug(f"  origin/HEAD points to {branch}")

    base = run_git("merge-base", "HEAD", "origin/HEAD")
    if base:
        debug(f"  found merge-base {base[:12]} with {branch}")
        return branch, "origin/HEAD"

    debug("  could not determine merge-base with origin/HEAD")
    return None, None


def try_common_default_branches() -> tuple[str | None, str | None]:
    """Try common default branch names on origin."""
    debug("Trying common default branches")
    for branch in ["origin/main", "origin/master", "origin/develop", "origin/dev"]:
        debug(f"  checking {branch}")
        if run_git("rev-parse", "--verify", branch):
            base = run_git("merge-base", "HEAD", branch)
            if base:
                debug(f"  found merge-base {base[:12]} with {branch}")
                return branch, "common default branch"
        else:
            debug(f"  {branch} does not exist")

    return None, None


def get_existing_remotes() -> list[str]:
    """Get list of configured remotes."""
    output = run_git("remote")
    if not output:
        return []
    return [r.strip() for r in output.splitlines() if r.strip()]


def should_skip_branch(remote_branch: str, current_branch: str | None) -> bool:
    """Determine if a remote branch should be skipped.

    Skip the current branch's remote tracking branch, unless it's
    a default branch (main, master, etc.) - in that case we still
    want to compare against the remote to see unpushed commits.
    """
    if not current_branch:
        return False

    if not remote_branch.endswith(f"/{current_branch}"):
        return False

    if current_branch in DEFAULT_BRANCH_NAMES:
        debug(f"    including {remote_branch} (tracking branch for default branch)")
        return False

    debug(f"    skipping {remote_branch} (tracking branch for feature branch)")
    return True


def get_branch_distance(remote_branch: str) -> tuple[str, int] | None:
    """Get the merge-base and commit distance for a remote branch.

    Returns tuple of (merge_base_sha, distance) or None if not determinable.
    """
    base = run_git("merge-base", "HEAD", remote_branch)
    if not base:
        return None

    count_output = run_git("rev-list", "--count", f"{base}..HEAD")
    if not count_output:
        return None

    return base, int(count_output)


def find_closest_branch_for_remote(
    remote: str,
    remote_branches: list[str],
    current_branch: str | None,
) -> str | None:
    """Find the closest branch for a single remote."""
    branches_for_remote = [b for b in remote_branches if b.startswith(f"{remote}/")]
    if not branches_for_remote:
        debug(f"    no branches for {remote}")
        return None

    best_branch = None
    min_distance = float("inf")

    for remote_branch in branches_for_remote:
        if should_skip_branch(remote_branch, current_branch):
            continue

        result = get_branch_distance(remote_branch)
        if not result:
            continue

        base, distance = result
        debug(f"    {remote_branch}: merge-base {base[:12]}, distance {distance}")

        if distance < min_distance:
            min_distance = distance
            best_branch = remote_branch

    if best_branch:
        debug(f"  best from {remote}: {best_branch} with distance {min_distance}")

    return best_branch


def try_closest_remote_branch() -> tuple[str | None, str | None]:
    """Find the closest remote branch by commit distance.

    Only considers branches from preferred remotes (in priority order).
    Remotes earlier in PREFERRED_REMOTES take precedence.
    """
    debug("Trying closest remote branch by commit distance")
    debug(f"  preferred remotes: {PREFERRED_REMOTES}")

    existing_remotes = get_existing_remotes()
    debug(f"  existing remotes: {existing_remotes}")

    remotes_to_check = [r for r in PREFERRED_REMOTES if r in existing_remotes]
    if not remotes_to_check:
        debug("  no preferred remotes found")
        return None, None

    debug(f"  checking remotes: {remotes_to_check}")

    remote_branches = get_remote_branches()
    if not remote_branches:
        debug("  no remote branches found")
        return None, None

    current_branch = run_git("branch", "--show-current")
    debug(f"  current branch: {current_branch}")

    for remote in remotes_to_check:
        debug(f"  checking remote: {remote}")
        best_branch = find_closest_branch_for_remote(
            remote, remote_branches, current_branch
        )
        if best_branch:
            return best_branch, "closest remote branch"

    debug("  no suitable branch found in any preferred remote")
    return None, None


def find_base_branch() -> tuple[str | None, str | None]:
    """Find the base branch for the current branch.

    Tries strategies in order:
    - @{upstream} (the current branch's configured upstream)
    - origin/HEAD (the remote's default branch)
    - Common default branch names (main, master, develop, dev)
    - Closest remote branch by commit distance

    Returns:
        Tuple of (branch_name, source_description)
    """
    strategies = [
        try_upstream,
        try_common_default_branches,
        try_closest_remote_branch,
        try_origin_head,
    ]

    for strategy in strategies:
        base, source = strategy()
        if base:
            return base, source

    return None, None


def main() -> int:
    global DEBUG

    parser = argparse.ArgumentParser(
        description="Find the merge base commit for the current branch"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show how the merge base is determined",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch latest remote refs before determining merge base",
    )
    args = parser.parse_args()

    DEBUG = args.debug

    # Ensure we're in a git repository
    if not run_git("rev-parse", "--git-dir"):
        print("Error: not a git repository", file=sys.stderr)
        return 1

    if args.fetch:
        debug("Fetching latest remote refs")
        run_git("fetch", "--prune", "--quiet")

    branch, source = find_base_branch()
    if not branch:
        print("Error: could not determine base branch", file=sys.stderr)
        return 1

    debug(f"Result: {branch} (via {source})")
    print(branch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
