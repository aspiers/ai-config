# s6-overlay 3.2.3.2 Artifact Audit

**Verdict: BLOCKED — do not add these release binaries to the orchestrator
image.**

The official x86-64 and noarch archives match their published checksums and
contain no escaping paths or links. However, the architecture archive contains
142 stripped static ELF executables, including a setuid-root bootstrap helper,
and the upstream release build is not an immutable or checksum-complete supply
chain. The executables were not reproduced from the reviewed source.

## Identity and provenance

| Item | Reviewed identity |
| --- | --- |
| repository | [`just-containers/s6-overlay`](https://github.com/just-containers/s6-overlay) |
| source commit | [`60b2520427f27af3867ebd8de27c3a3b55346bef`](https://github.com/just-containers/s6-overlay/commit/60b2520427f27af3867ebd8de27c3a3b55346bef) |
| release | [`v3.2.3.2`](https://github.com/just-containers/s6-overlay/releases/tag/v3.2.3.2) |
| x86-64 archive | `sha256:e6befcc96a437a3831386ecfc51808c5d3e939dc5fe3c02ae9284599e8aa2408` |
| noarch archive | `sha256:5379750ed30a84bbd2e2dd74847ba6b5bd29cd0b2e3ea2ec58049b57eb2eda12` |
| audit date | 2026-08-01 |

The annotated release tag and source commit are unsigned. GitHub records SHA-256
digests on the assets, and the separately published `.sha256` files agree, but
both checksums and archives come from the same release channel. No SLSA/GitHub
artifact attestation was available for the noarch archive; x86-64 attestation
verification did not complete within the audit timeout.

## Artifact inventory

The required minimal pair was downloaded without execution, checksum-verified,
compression-tested, listed, and extracted into a temporary inspection tree:

| Archive | Entries | Regular files | Symlinks | Escaping paths/links |
| --- | ---: | ---: | ---: | ---: |
| `s6-overlay-noarch.tar.xz` | 76 | 40 | 6 | 0 |
| `s6-overlay-x86_64.tar.xz` | 548 | 154 | 365 | 0 |

The architecture archive contains 142 stripped, statically linked x86-64 ELF
executables from skalibs, execline, s6, s6-rc, s6-linux-init,
s6-portable-utils, s6-linux-utils, s6-dns, s6-networking, BearSSL, and the
overlay helpers. The remaining regular files are package metadata and text.
Symlinks under `/command` resolve within the overlay root.

## Execution and privilege surface

`/init` becomes PID 1. It executes `s6-overlay-suexec`, asks it to run `preinit`,
then runs `stage0` and the generated s6 init tree. The archive installs
`s6-overlay-suexec` as mode `4755` and owner root.

`preinit` normally executes with effective UID 0. It can:

- create or remount `/run` as executable tmpfs, potentially requiring
  `CAP_SYS_ADMIN`;
- change `/run` ownership and permissions;
- replace `/var/run` with a symlink to `/run`;
- recursively remove stale `/run/s6*`, `/run/service`, and log state;
- prepare runtime service directories before dropping to the configured
  container user.

The source supports fully unprivileged operation when setuid is denied and the
container manager has already prepared a secure executable `/run`. That mode
must be enforced explicitly for the cockpit. Installing the archive unchanged
conflicts with the contract's requirement that the OCI runtime remain
unprivileged after namespace setup because it adds a setuid-root executable and
attempts a privileged pre-initialization path.

After bootstrap, s6 supervises arbitrary service definitions supplied by the
image. It reads container environment into `/run/s6/container_environment`,
changes ownership/modes described by `/etc/fix-attrs.d`, executes initialization
and finish scripts, and forwards signals/shutdown. It performs no inherent
telemetry or update check at runtime.

## Build and supply-chain review

The release workflow builds on GitHub-hosted `ubuntu-latest` runners and uses:

- `actions/checkout@v6.0.2` and `ncipollo/release-action@v1.21.0`, both mutable
  tags rather than immutable action commits;
- an x86-64 musl cross-toolchain downloaded from `skarnet.org` without a pinned
  checksum or signature;
- BearSSL at a full commit;
- ten other skarnet/overlay projects selected by mutable version tags;
- unauthenticated `git://git.skarnet.org/...` clones for the skarnet projects;
- local stripping followed by GNU tar/xz packaging and release-uploaded
  checksums.

The workflow does not record resolved dependency commits, toolchain digest,
build image digest, compiler identity, or reproducibility comparison. A tag or
download could resolve differently at rebuild time, and the downloaded
cross-toolchain is trusted before any integrity check. Therefore the 142 release
binaries cannot be connected byte-for-byte to the reviewed overlay commit and
immutable dependency inputs.

## Scanner results

- Gitleaks found no candidate secrets in the source checkout.
- Archive path and symlink containment checks passed.
- `file(1)` confirmed static stripped ELF payloads; static linkage prevents a
  conventional host shared-library vulnerability scan.
- No ecosystem lockfile or SBOM was supplied for the C dependency graph.
- Candidate programs, build commands, tests, init, and service entrypoints were
  not executed.

## Consequence, remediation, and trigger

Adding this release would put an unreproduced setuid-root binary and more than a
hundred opaque privileged/runtime executables at the base of every cockpit
process. A compromised action tag, dependency tag, download, toolchain, or
release upload could gain control before Herdr, Collie, or AgentBox starts.

A re-audit may pass only after the deployment either:

1. builds from a vendored/checksummed toolchain and full immutable dependency
   SHAs, compares the result to the release, and records an SBOM; or
2. uses distribution-provided s6 packages with independently verified package
   signatures and source provenance, plus only reviewed noarch overlay scripts.

In both cases, remove/disable setuid on `s6-overlay-suexec`, prepare `/run` in
the OCI definition, drop all capabilities including `CAP_SYS_ADMIN`, set
`no-new-privileges`, and prove the unprivileged startup path in the later
approval-gated behavioral test.

Rollback/removal trigger for any later approved build: an effective UID 0 after
namespace setup, a setuid file in the final image, unexpected mount attempt,
write outside declared runtime paths, checksum/provenance mismatch, or service
execution not present in the reviewed image definition.

**Approved by user:** not requested; a blocked audit cannot be approved for
first execution.
