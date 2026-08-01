# Herdr 0.7.5 Runtime Audit

**Verdict: INCOMPLETE — source review found no malicious path, but do not add
the release binary to a new orchestrator image yet.**

The installed Linux x86-64 binary exactly matches the official release digest,
and the release build is substantially better pinned than the other reviewed
cockpit components. The binary is nevertheless an unattested unsigned opaque
artifact that was not reproduced during this audit. Reproduction is candidate
execution and requires the explicit approval gate.

## Identity and provenance

| Item | Reviewed identity |
| --- | --- |
| repository | [`herdrdev/herdr`](https://github.com/herdrdev/herdr) |
| release | [`v0.7.5`](https://github.com/herdrdev/herdr/releases/tag/v0.7.5) |
| source commit | [`ef4c23f5775bb8cfec05f05d0844226ff959a07a`](https://github.com/herdrdev/herdr/commit/ef4c23f5775bb8cfec05f05d0844226ff959a07a) |
| Linux x86-64 artifact | `sha256:3dc83288073e4c2d3c679a30e7be97bcca9141c6fd17dbbb9219142e95c59253` |
| artifact size | 21,315,048 bytes |
| audit date | 2026-08-01 |

The annotated tag and commit are unsigned. GitHub records the same SHA-256 on
the release asset. The currently installed `~/.local/bin/herdr` is mode `0755`,
owned by the user, is a non-stripped static PIE, and matches that digest. GitHub
has no SLSA attestation for it.

## Scope and build chain

- Inventoried all 1,879 tracked files, one contained `CLAUDE.md -> AGENTS.md`
  symlink, no submodules, and no required LFS objects.
- The tree includes 266 Rust source files, 31 test files, and 1,259 vendored
  files (about 19 MiB).
- `Cargo.lock` pins registry package versions and checksums. `portable-pty` is a
  local patched dependency. `libghostty-vt` is vendored from commit
  `c5a21edfcbc2d5b46540ad91b7980aca31f5f1f3`.
- `build.rs` executes Zig against the vendored terminal library and links the
  result statically; it does not download code.
- The release workflow pins third-party GitHub Actions to commits, pins Rust
  1.96.1 and Zig 0.15.2, and runs `cargo build --release --locked`.

Remaining reproducibility gaps are mutable `ubuntu-latest`, apt packages from
live mirrors, caches, and no published build-info/SBOM/reproducibility result.
The release workflow uploads the binary but no provenance attestation.

## Runtime execution surface

Herdr is intentionally an unsandboxed terminal multiplexer and control plane.
It:

- spawns the configured shell and arbitrary user commands in PTYs;
- exposes a local Unix-socket API that can create/control panes and send text or
  keys to live terminals;
- runs plugin build, startup, event, action, pane, and link-handler commands as
  the current user;
- invokes Git for worktree discovery/creation/removal and status;
- invokes SSH for remote Herdr sessions and can download a matching remote
  binary;
- opens URLs, reads/writes clipboard content, emits desktop notifications, and
  runs audio helpers;
- persists configuration, sessions, logs, sockets, plugin state, and staged
  clipboard images under XDG/user state paths.

These capabilities are expected but make Herdr equivalent to the orchestrator
user. The Unix API and handoff sockets use owner-restricted paths/modes in the
reviewed implementation. Plugins remain arbitrary code and must not be copied
from the laptop into the cockpit merely because they are already registered
there.

## Network and update behavior

Version and agent-manifest checks are enabled by default and run every 30
minutes. Herdr invokes `curl` to fetch manifests from `herdr.dev`. The explicit
update path downloads and atomically replaces the running binary; it verifies
SHA-256 only when the manifest supplies one. Remote-session setup can likewise
download a target binary selected by a remote manifest.

The cockpit configuration must set both update checks false, prohibit self
update, pin the image binary by digest, and upgrade only through a fresh audit.
No unreviewed plugin marketplace install or remote-binary download is allowed in
the image.

## Dependency and scanner findings

`cargo audit` reported no vulnerability-class advisories, but reported:

- `RUSTSEC-2026-0190`: `anyhow 1.0.102` unsound `Error::downcast_mut`, fixed in
  1.0.103;
- `RUSTSEC-2026-0097`: `rand 0.8.5` unsound under a custom logger/reseeding
  combination, fixed in 0.8.6;
- `RUSTSEC-2025-0141`: unmaintained `bincode 2.0.1`;
- yanked `unicode-segmentation 1.13.1`.

No use of `downcast_mut`, `thread_rng`, `rand::rng`, or a custom `log::Log`
implementation was found in the reviewed Herdr/vendored source, so the known
unsound paths do not appear reachable. They should still be upgraded before a
long-lived control-plane build.

Gitleaks reported five heuristic matches in the vendored libghostty tree. Four
are GitHub workflow secret-expression names without values; the fifth is a key
binding test string. No credential value was found.

Candidate builds, tests, binaries, update paths, plugins, and runtime commands
were not executed during this audit. Static review and scanners cannot prove the
absence of malicious or dormant behavior.

## Prerequisite, verification, and rollback

Before first cockpit execution:

1. obtain explicit approval to build the exact source in a disposable,
   credential-free environment;
2. run the locked Rust/Zig build with pinned base-image and apt snapshot inputs;
3. compare the resulting binary with the release digest or explain every
   deterministic difference;
4. upgrade or formally prove unreachable the two unsound dependencies;
5. generate an SBOM and scan the reproduced static binary; and
6. configure `update.version_check = false` and `update.manifest_check = false`
   before startup.

For the isolated behavioral test, mount only temporary XDG state, no production
plugins or credentials, and verify socket permissions, filesystem writes,
network silence, subprocesses, and clean shutdown.

Rollback/removal trigger for a later approved build: unconfigured egress,
self-update/download, socket access by another user, unexpected plugin/process,
write outside declared volumes, checksum mismatch, or a reachable critical/high
advisory.

**Approved by user:** pending; no candidate execution was requested.
