#!/bin/sh
#
# Example only: adapt the file list and setup steps to the target repository.
#
# Makes a new git worktree of this repository usable straight away. Both
# worktrunk (.config/wt.toml pre-start) and Orca (orca.yaml scripts.setup)
# call this, so every worktree gets the same setup however it was created.
# Safe to re-run: every step either skips work already done or is itself
# idempotent.
#
# Usage: sh scripts/worktree-setup.sh [primary-checkout-path]
#
# Run from anywhere inside the new worktree. The primary checkout defaults
# to the one owning the shared .git directory, so no tool-specific
# environment variable is needed.

set -e

cd "$(git rev-parse --show-toplevel)"

# The primary checkout owns the shared .git directory. Pass the path
# explicitly where that is not true, e.g. a bare-repository layout.
primary="${1:-$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")}"

# Gitignored files the app reads at runtime. Each is linked, not copied, so
# a rotated secret reaches every worktree from one source of truth.
LOCAL_FILES=".env.local"

if [ "$(pwd -P)" = "$(cd "$primary" && pwd -P)" ]; then
    echo "worktree setup: in the primary checkout; skipped linking local files."
else
    for file in $LOCAL_FILES; do
        # A dangling link fails `-e`, so `-L` stops `ln` from aborting a re-run
        # under `set -e` after the primary's file was removed.
        if [ -e "$file" ] || [ -L "$file" ]; then
            echo "worktree setup: $file already present; left untouched."
        elif [ -f "$primary/$file" ]; then
            mkdir -p "$(dirname "$file")"
            ln -s "$primary/$file" "$file"
            echo "worktree setup: linked $file from the primary checkout."
        else
            echo "worktree setup: no $file in the primary checkout; skipped."
        fi
    done
fi

# Replace with this repository's own install and build steps. Hard failures
# should stop setup; steps that only fail on a flaky network can warn
# instead, as long as a later step would catch a genuinely broken install.
npm install
