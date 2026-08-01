# AgentBox 0.27.1 Runtime Audit

**Verdict: BLOCKED — do not use this release in the orchestrator image.**

The exact published release has known production dependency vulnerabilities,
including two critical and twenty high advisories in its pinned workspace lock.
The network-facing bundled Hub uses vulnerable Next.js 16.2.7 and has Server
Actions. The package also contains generated bundles that were not reproduced
byte-for-byte from source and an optional native dependency that was not present
in the tarball for review.

## Identity and provenance

| Item | Reviewed identity |
| --- | --- |
| npm package | `@madarco/agentbox@0.27.1` |
| npm integrity | `sha512-T+Zgqzwy/tKerS53Ow34Ehz0k/1Jn2gEQSrwQXZkde2MZrAlMQJzONw3BtNYUXr+YwgI9P6G79uvLadL6+lcrw==` |
| npm SHA-1 | `edb3501b8f9cc40621b2d436bcc9143ff077a932` |
| source commit | [`c9424ad090eb636ea355dbefc8a54b3d31eaa5a3`](https://github.com/madarco/agentbox/commit/c9424ad090eb636ea355dbefc8a54b3d31eaa5a3) |
| Herdr plugin | `agentbox` 0.2.0 at the same source commit |
| audit date | 2026-08-01 |

The registry's `gitHead` matches the reviewed unsigned source commit. Registry
integrity and signature metadata were present and the downloaded tarball matched
the recorded SHA-512 and SHA-1 values.

## Scope and payload reconciliation

- Inventoried 1,189 source files, three contained relative symlinks, no
  submodules, and no LFS dependency needed by the published package.
- Inventoried all 716 files in the 25 MiB unpacked npm payload. No native ELF,
  Mach-O, PE, WASM, or archive was embedded in that tarball.
- The payload contains generated CLI chunks and source maps, staged shell/Node
  runtimes for each provider, a bundled relay, and a 12 MiB standalone Next.js
  Hub build.
- Source maps and staged source paths provide substantial source correspondence,
  but the generated CLI, relay, and Next output were not reproducibly rebuilt.
  The standalone Hub includes generated data that `file(1)` cannot classify as
  text.
- The optional `@homebridge/node-pty-prebuilt-multiarch` dependency can add a
  native prebuilt during dependency installation. Its platform artifact and
  transitive install payload are outside this tarball and remain unreviewed.

Consequently, the executable payload is not fully reconciled to audited source.

## Herdr plugin execution surface

The root `herdr-plugin.toml` defines:

- build: `sh build.sh`;
- pane: `agentbox list --herdr --watch` through a generated absolute-path shim;
- actions: open the boxes pane, create a box, and open an `agentbox://` link;
- link handler: every URL beginning `agentbox://` routes to the open-link action;
- no startup or event hooks.

`build.sh` locates `agentbox` on `PATH` and invokes `agentbox install herdr
--plugin-keys`. That path writes an executable shim, modifies Herdr's
`config.toml`, adds keybindings, and reloads the server. The normal local install
also writes under `~/.agentbox/herdr/plugin`, may unlink an existing plugin after
a failed link, and links the generated plugin. Build failure is deliberately
converted to success, potentially leaving an inert or partially configured
plugin.

## Runtime and sensitive behavior

AgentBox is deliberately a high-authority host control plane:

- starts local containers and remote cloud sandboxes;
- executes Docker, SSH, Git, `gh`, browser-open, copy/download, and provider SDK
  operations;
- reads and writes repositories, `~/.agentbox`, managed SSH configuration,
  per-box keys, provider tokens, and AI-agent credentials;
- transfers repositories and selected credentials into remote boxes;
- downloads/builds provider runtimes and box images on demand;
- runs a long-lived relay and optional Hub.

The relay defaults to `0.0.0.0` because containers must reach it. Per-box bearer
and bridge tokens protect box and host-poller routes. Host-side Git, GitHub,
copy, download, checkpoint, browser, and integration operations have explicit
validation and approval paths. However, `AGENTBOX_PROMPT=off` and per-box
auto-approval settings intentionally bypass human prompts; safe-subset actions
also auto-approve. The orchestrator must not enable blanket bypasses.

The Hub defaults to loopback with a generated owner-only token, but its Hetzner
profile binds `0.0.0.0` and uses password authentication. It imports provider
SDKs, controls box lifecycle, presents approvals, and invokes Server Actions.
It therefore makes Next.js and authentication advisories production-relevant.

## Dependency and vulnerability findings

The workspace lock resolved 793 production dependencies. `pnpm 9.15.9 audit
--prod` returned 51 advisory records; its metadata counted 52 vulnerable
instances:

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 20 |
| Moderate | 27 |
| Low | 3 |

Blocking examples include:

- [`next@16.2.7`](https://github.com/advisories/GHSA-89xv-2m56-2m9x):
  server-side request forgery in Server Actions; fixed in 16.2.11.
- [`next@16.2.7`](https://github.com/advisories/GHSA-m99w-x7hq-7vfj):
  Server Action denial of service; fixed in 16.2.11.
- [`next@16.2.7`](https://github.com/advisories/GHSA-p9j2-gv94-2wf4):
  SSRF through attacker-controlled rewrite destinations.
- [`tar@7.5.15`](https://github.com/advisories/GHSA-23hp-3jrh-7fpw):
  critical decompression/parse denial of service; fixed in 7.5.19.
- `undici`, `axios`, `sharp`, `form-data`, `shell-quote`, and other packages
  also have high advisories in the pinned resolution.

The other critical advisory targets the development-only Vitest UI and does not
make the published CLI runtime exploitable by itself. It still demonstrates that
the source lock is not currently clean.

## Scanner results

- Gitleaks found no candidates in the source checkout.
- Gitleaks reported three values in the published Next output. They are generated
  preview/signing/encryption keys, not developer credentials. Because the same
  static values are public in every copy of this npm artifact, their use by
  Next preview mode or Server Actions requires upstream security review and
  runtime regeneration where supported.
- Static file classification found no embedded native executable in the npm
  tarball.
- Candidate builds, installs, tests, lifecycle scripts, binaries, and runtime
  entrypoints were not executed.

## Consequence, remediation, and trigger

Using 0.27.1 would place a credential-bearing control plane and network-facing
Hub on known-vulnerable dependencies. A crafted authenticated or otherwise
reachable request could cause SSRF, denial of service, or exploit another
advisory-specific path; archive processing also carries a critical resource
exhaustion risk.

Re-audit a newer exact release only after it:

1. upgrades Next.js to at least 16.2.11 and `tar` to at least 7.5.19;
2. resolves or explicitly proves unreachable every remaining critical/high
   production advisory;
3. supplies a reproducible mapping for generated CLI/relay/Hub files; and
4. identifies and audits the exact native PTY prebuild selected for the target.

Rollback/removal trigger for any later approved trial: unexpected public bind,
authentication bypass, unprompted host action, secret appearing in a box/log,
or any new critical/high reachable advisory.

**Approved by user:** not requested; a blocked audit cannot be approved for
first execution.
