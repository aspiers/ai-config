# Portable AI Cockpit Orchestrator Contract

> **⚠️ AUTHOR-SPECIFIC WORKFLOW:** This deployment supports the maintainer's
> private cockpit plan. Other installations must substitute their own private
> plan and local configuration. Never commit hostnames, addresses, account
> identifiers, credentials, private repository URLs, actual costs, or secret
> values to this directory.

This contract defines one target-neutral orchestrator runtime for either an
isolated always-on local host or a small cloud VPS. Target selection happens
only after both environments are evaluated against the same acceptance matrix.

The orchestrator is a trusted control plane. It coordinates AgentBox boxes
hosted elsewhere; it MUST NOT run local AgentBox boxes, mount a Docker socket,
or pass broad orchestrator credentials into a box.

## Invariants

- The laptop and phone are disposable clients, not runtime dependencies.
- Agent execution occurs only on remote AgentBox providers.
- All inbound access is through Tailscale or SSH restricted to the tailnet.
- Provider, Git, and agent credentials remain on the orchestrator and are
  injected as secret files.
- The same image, paths, service definitions, probes, backup scripts, and
  recovery commands run on local and VPS targets.
- Persistent volumes can move between targets without changing client flows.
- No service binds a publicly reachable host interface.

## Runtime Identity and Layout

The OCI container runs as the unprivileged `cockpit` user.
Deployments SHOULD map its UID and GID to dedicated host IDs and MUST NOT run it
as root after initial namespace setup.

| Purpose | Container path | Persistent volume | Contents |
| ------- | -------------- | ----------------- | -------- |
| Home | `/home/cockpit` | `cockpit-home` | Minimal application home and user configuration |
| Herdr | `/state/herdr` | `cockpit-herdr` | Herdr socket, database, layouts, and session metadata |
| Collie | `/state/collie` | `cockpit-collie` | Collie configuration and application state |
| AgentBox | `/state/agentbox` | `cockpit-agentbox` | Queue, relay, provider metadata, and recovery state |
| Tailscale | `/state/tailscale` | `cockpit-tailscale` | Tailscale node state when Tailscale runs in the bundle |
| Repositories | `/repos` | `cockpit-repos` | Source checkouts used only to seed remote boxes |
| Backups | `/backup` | `cockpit-backups` | Encrypted backup archives and verification manifests |

Compatibility links under `/home/cockpit` MAY point into these volumes, such as
`~/.agentbox` to `/state/agentbox`. Credentials are not stored in these
volumes unless an application cannot consume a secret file and the documented
exception is encrypted at rest.

The application image and service configuration are read-only. Writable
runtime paths are limited to the table above, `/run`, and `/tmp`.

## Components and Supervision

One rootless OCI bundle contains these long-running processes:

1. `herdr` — persistent server using a Unix socket under `/state/herdr`.
2. `collie` — mobile PWA bound only to container loopback.
3. `agentbox-relay` — AgentBox queue and host relay.
4. `tailscaled` — optional when the container owns its tailnet identity.
5. `sshd` — optional tailnet-only administrative and client endpoint.

`s6-overlay` is the in-container supervisor. Each process has an independent
service directory, readiness check, bounded restart backoff, and stdout/stderr
forwarded to the container logger. A failure in Collie MUST NOT terminate Herdr
or the AgentBox relay.

The host uses systemd to supervise the rootless bundle:

- `ai-cockpit.service` starts the Compose/Podman unit after networking and
  restarts it after failure or reboot.
- `ai-cockpit-backup.service` runs one encrypted snapshot and verification.
- `ai-cockpit-backup.timer` schedules backups with randomized delay.
- `ai-cockpit-restore-test.service` performs a periodic disposable restore and
  runs the health probe against it.

User services require lingering where the host implementation uses a user
systemd manager. The deployment MUST start after power loss without an
interactive login.

## Network Contract

### Ingress

- Tailscale HTTPS exposes Collie through `tailscale serve`; Funnel is forbidden.
- Herdr remote access uses its Unix socket through an authenticated Tailscale or
  SSH transport.
- SSH listens only on the Tailscale interface or is firewall-restricted to the
  tailnet.
- Component HTTP ports bind to `127.0.0.1` inside the orchestrator namespace.
- The host firewall denies unsolicited public ingress by default.

Tailscale ACLs SHOULD grant laptop and phone identities only the services they
need. Administrative SSH and mobile Collie access SHOULD use separate grants.

### Egress

The orchestrator may initiate:

- AgentBox provider API and SSH connections;
- Git forge HTTPS/SSH connections;
- package and image registry HTTPS connections;
- Tailscale control and DERP connections;
- configured monitoring and encrypted backup destinations.

Remote boxes connect back only through the scoped AgentBox relay protocol.
They receive no Docker socket, orchestrator filesystem mount, or general-purpose
credential directory.

## Secret Injection

Secrets are supplied at runtime as owner-only files beneath `/run/secrets`.
The committed `env.example` contains names and harmless placeholders only.

Secret classes are:

- AgentBox provider credentials;
- repository-scoped Git forge credentials;
- SSH keys or short-lived SSH certificates;
- AI-agent authentication;
- Tailscale authentication material;
- backup encryption and destination credentials;
- Collie trusted-user configuration.

The image, Compose file, logs, health output, backups manifests, and environment
inventory MUST NOT contain secret values. Secret files use mode `0600`; their
directory uses mode `0700`. Prefer short-lived or repository-scoped credentials
and rotate any credential exposed to a remote box.

## Health Contract

`bin/ai-cockpit-healthcheck` returns non-zero when any mandatory check fails and
emits no secret values. It checks:

| Check | Success condition |
| ----- | ----------------- |
| Supervisor | Every mandatory s6 service is up and outside restart backoff |
| Herdr | Unix socket exists and a bounded status request succeeds |
| Collie | Loopback readiness endpoint returns success |
| AgentBox relay | Relay status reports ready and its state directory is writable |
| Remote-only boxes | No local Docker/Podman box runtime or mounted Docker socket is detected |
| Tailscale | Node is authenticated and required serve routes are active |
| Storage | Persistent volumes are writable and remain above configured free-space thresholds |
| Backup | Latest verified encrypted backup is younger than the configured maximum age |

The container declares this script as its OCI health check. Monitoring alerts on
three consecutive failures and distinguishes control-plane degradation from a
remote provider outage.

## Startup and Recovery

Target-neutral startup:

```sh
podman compose --env-file ~/.config/ai-cockpit/runtime.env \
  -f deploy/ai-cockpit/compose.yaml up -d
podman exec ai-cockpit bin/ai-cockpit-healthcheck
```

Control-plane recovery after restart:

```sh
podman exec ai-cockpit agentbox relay start
podman exec ai-cockpit agentbox recover --all --no-attach
podman exec ai-cockpit bin/ai-cockpit-healthcheck
```

A recovery run MUST be idempotent. Remote boxes may continue computing during
an orchestrator outage, but queue dispatch, Collie, approvals, relay-mediated
Git operations, and orchestrator-hosted forwards remain unavailable until
recovery succeeds.

## Backup and Restore

`bin/ai-cockpit-backup` pauses only components that require a consistent
snapshot, archives every named persistent volume, encrypts before leaving the
host, writes a checksum manifest, and resumes services even on failure.
Repository checkouts MAY be recreated from remotes, but unpushed work and relay
state MUST be included.

`bin/ai-cockpit-restore` accepts a new empty volume root and never overwrites a
running deployment. A restore test MUST:

1. restore the latest archive to disposable volumes;
2. start the same image with network egress disabled where practical;
3. pass structural volume checks and component health probes;
4. verify AgentBox queue metadata and repository checkout integrity;
5. destroy the disposable restore after recording the result.

Migration between local and VPS targets uses the same restore command. The old
target remains stopped but intact until the new target passes health and client
acceptance checks.

## Client Contract

- Laptop terminal control uses Herdr remote access or a mirror client.
- Phone control uses tailnet-only Collie HTTPS.
- Public-preview provider URLs are printed remotely and opened on the laptop.
- SSH-backed box previews and noVNC use laptop-side `ProxyJump` and
  `LocalForward`; orchestrator-loopback URLs are never presented as laptop
  URLs.
- IDE access uses laptop-side Remote SSH through the orchestrator jump host.
- Ordinary text travels as terminal input.
- Image/file transfer uses an explicit upload path until AgentBox supports
  headless orchestrator file interception independently of clipboard capture.

## Target-Neutral Acceptance Matrix

Record measurements in ignored local configuration or the private decision
record, never in this public repository.

| Criterion | Local target evidence | VPS target evidence | Pass rule |
| --------- | --------------------- | ------------------- | --------- |
| Availability | Reboot, power-loss, sleep-prevention, and ISP-outage exercises | Reboot, provider-maintenance, and network-outage exercises | Services recover without interactive login and meet the private availability objective |
| Laptop latency | Herdr attach, typing, approval, and preview timing | Same measurements | Both remain usable on representative roaming networks |
| Phone latency | Collie load, pane update, reply, and special-key timing | Same measurements | Tailnet-only interaction remains responsive |
| Box seeding | Timed upload of a representative public-safe fixture repository | Same fixture and provider | Meets the private qualitative workflow threshold |
| Security blast radius | Host isolation, firewall, ACL, mount, and credential review | Public-host hardening, firewall, ACL, and credential review | No public service, Docker socket, broad host mount, or box credential leakage |
| Recovery | Backup, disposable restore, and orchestrator replacement drill | Same drill | Restored target passes health and client checks |
| Qualitative cost | Power, maintenance, and opportunity-cost category | Recurring service tier category | User records an explicit acceptable choice without committing actual costs |
| Volume migration | Restore local volumes on a disposable VPS-shaped target | Restore VPS volumes on a disposable local-shaped target | No path, image, or client-workflow change is required |

## Deployment Decision Gate

Do not provision a paid target or make an irreversible host change until:

1. both targets have complete matrix evidence;
2. unresolved browser, IDE, port-forwarding, and file-transfer gaps are listed;
3. backup and migration drills pass;
4. the user explicitly selects a target in the private decision record.

The selected location may change later. The runtime contract does not.
