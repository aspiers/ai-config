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
// Usage: node scripts/worktree-setup.mts

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, realpathSync, symlinkSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

// Gitignored files the app reads at runtime. Each is linked, not copied, so
// a rotated secret reaches every worktree from one source of truth.
const LOCAL_FILES = [".env.local"];

export type LinkResult = "linked" | "present" | "no-source";

function git(cwd: string, args: string[]): string {
    // Piped stderr keeps an expected failure (see primaryCheckout) quiet.
    return execFileSync("git", args, {
        cwd,
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
    }).trim();
}

/**
 * The first `git worktree list` entry is the main worktree, under worktrunk,
 * Orca and plain `git worktree add` alike. For a bare repository, or one
 * made with --separate-git-dir, that entry is the metadata directory rather
 * than a checkout, so it is trusted only if it is its own work tree.
 * Otherwise this returns null rather than guessing: a guessed directory,
 * such as the parent of a bare repo, could hold an unrelated .env.local.
 */
export function primaryCheckout(cwd: string): string | null {
    const [entry] = git(cwd, ["worktree", "list", "--porcelain", "-z"]).split(
        "\0",
    );
    const candidate = entry.replace(/^worktree /, "");
    try {
        const top = git(candidate, ["rev-parse", "--show-toplevel"]);
        return realpathSync(top) === realpathSync(candidate) ? candidate : null;
    } catch {
        return null;
    }
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

export function install(
    cwd: string,
    platform: NodeJS.Platform = process.platform,
): number {
    // Replace with this repository's own install and build steps. Windows
    // needs a shell to resolve the npm.cmd shim, and since CVE-2024-27980
    // Node refuses to spawn a .cmd file without one, so naming npm.cmd is
    // no fix. A shell is safe here only because the arguments are constant.
    const { status, error } = spawnSync("npm", ["install"], {
        cwd,
        stdio: "inherit",
        shell: platform === "win32",
    });
    if (error) {
        throw error;
    }
    return status ?? 1;
}

interface MainOptions {
    cwd?: string;
    runInstall?: (cwd: string) => number;
}

/** Returns the install's exit code. */
export function main({
    cwd = process.cwd(),
    runInstall = install,
}: MainOptions = {}): number {
    const worktree = git(cwd, ["rev-parse", "--show-toplevel"]);
    const primary = primaryCheckout(cwd);
    if (primary === null) {
        console.log(
            "No primary checkout (bare repository or separate git dir); skipped linking local files.",
        );
    } else if (realpathSync(primary) === realpathSync(worktree)) {
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
    process.exitCode = main();
}
