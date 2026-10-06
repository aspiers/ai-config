#!/usr/bin/env node
// Example only: adapt the file list and setup steps to the target repository.
//
// Makes a new git worktree of this repository usable straight away. Both
// worktrunk (.config/wt.toml pre-start) and Orca (orca.yaml scripts.setup)
// call this, so every worktree gets the same setup however it was created.
// Safe to re-run: existing files are never replaced, and a repeat install
// is a no-op.
//
// It runs before dependencies are installed, so it uses only Node
// built-ins. Node >= 22.18 strips TypeScript types natively, so no tsx is
// needed: keep to erasable syntax (no enums, namespaces or parameter
// properties). The .mts extension makes it ESM without Node's
// typeless-package warning.
//
// Usage: node scripts/worktree-setup.mts [primary-checkout-path]

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, realpathSync, symlinkSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

// Gitignored files the app reads at runtime. Each is linked, not copied, so
// a rotated secret reaches every worktree from one source of truth.
const LOCAL_FILES = [".env.local"];

export type LinkResult = "linked" | "present" | "no-source";

function git(cwd: string, args: string[]): string {
    return execFileSync("git", args, { cwd, encoding: "utf8" }).trim();
}

/**
 * The primary checkout owns the shared .git directory, so it is the parent
 * of --git-common-dir. This works for worktrunk, Orca and plain
 * `git worktree add` alike, without reading any tool's environment.
 */
export function primaryCheckout(cwd: string): string {
    return path.dirname(
        git(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"]),
    );
}

export function linkLocalFile(
    primary: string,
    worktree: string,
    file: string,
): LinkResult {
    const source = path.join(primary, file);
    if (!existsSync(source)) {
        return "no-source";
    }
    const target = path.join(worktree, file);
    mkdirSync(path.dirname(target), { recursive: true });
    try {
        // symlinkSync refuses any existing path, dangling links included, so
        // "never replace" needs no separate, racy existence check.
        symlinkSync(source, target);
    } catch (error) {
        if ((error as NodeJS.ErrnoException).code === "EEXIST") {
            return "present";
        }
        throw error;
    }
    return "linked";
}

function install(cwd: string): number {
    // Replace with this repository's own install and build steps.
    const { status, error } = spawnSync("npm", ["install"], {
        cwd,
        stdio: "inherit",
    });
    if (error) {
        throw error;
    }
    return status ?? 1;
}

interface MainOptions {
    cwd?: string;
    primary?: string;
    runInstall?: (cwd: string) => number;
}

/** Returns the install's exit code. */
export function main({
    cwd = process.cwd(),
    primary = primaryCheckout(cwd),
    runInstall = install,
}: MainOptions = {}): number {
    const worktree = git(cwd, ["rev-parse", "--show-toplevel"]);
    if (realpathSync(primary) === realpathSync(worktree)) {
        console.log("In the primary checkout; skipped linking local files.");
    } else {
        for (const file of LOCAL_FILES) {
            console.log(`${file}: ${linkLocalFile(primary, worktree, file)}`);
        }
    }
    return runInstall(worktree);
}

if (
    process.argv[1] &&
    import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
) {
    process.exitCode = main(
        process.argv[2] ? { primary: process.argv[2] } : {},
    );
}
