---
name: managing-orca-plugins
description: >-
  Audits, installs, pins, approves, updates and removes third-party Orca
  plugins (orca-plugin.json, the Orca plugin catalog, Git URL installs and
  development folders), including trusted-worker plugins that reach Orca's
  runtime socket. Use before installing, enabling, approving or updating any
  Orca plugin, when asked whether an Orca plugin is safe, and when reviewing
  Orca plugin updates. For writing an Orca plugin, use Orca's own
  orca-plugin-authoring guide instead.
---

# Managing Orca plugins

Load `auditing-third-party-plugins` first: it owns the principles, the audit
procedure and the verdicts. This skill adds Orca's execution model, its
approval and update behaviour, and how to install a plugin so that it stays
on the audited code. Use `orca-cli-local` alongside it for general Orca CLI
rules.

Facts below were checked against Orca 1.4.251's CLI and the `stablyai/orca`
docs on 2026-11-07. Orca's plugin system moves quickly: re-check
`orca plugin --help` and the docs named here before relying on a detail.

## Execution profiles and effective authority

The manifest's `execution` field caps what a plugin may contribute:

- `data`: themes, syntaxes, translations. No code; installs without review.
- `declarative`: commands that run built-in Orca actions, shortcuts, VM
  recipes.
- `sandboxed-ui`: panels and custom editors in an isolated frame that can
  call only the host methods offered to panels. Orca's manifest docs still
  call panel and editor entries "trusted code".
- `trusted-worker`: a `main` Node module that Orca's approval prompt
  describes as running "in a separate Node.js process on the Orca host, with
  your user account's access to that machine". Events, hooks and worker
  commands need it.

For a `trusted-worker`, the declared capabilities only limit the plugin host
API. The worker can still read files and open sockets as the user. In
particular it can read `orca-runtime.json` in Orca's data folder, take the
runtime socket and auth token the `orca` CLI uses, and call the runtime
directly. How far Orca scopes that token was not checked; until it is,
treat effective authority as "whatever the `orca` CLI can do, plus the
user's files and network". Report the gap between that and the approval
prompt.

Watch for contributions that act without the user: `contributes.events`,
`contributes.hooks`, commands with `replaces` (they take over a built-in
action's shortcut and menu entry), and `statusBarItems`, which keep a
worker running for as long as the plugin is enabled.

## Auditing

- Fetch the source into an empty directory as the shared procedure
  describes, and run Orca's static tools on it: `orca plugin validate <dir>`
  and `orca plugin inspect <dir> --json`. `inspect` prints the grants the
  approval prompt will show and the content hash Orca will compute.
- `orca plugin test` and `orca plugin check` run plugin code unsandboxed.
  They fall under the execution freeze.
- Images in a manifest are data, but check that they are what their
  extension says.
- Add to the first-pass search: `orca-runtime`, `authToken`, `ui.set`,
  `terminal`, `agent`, and any runtime method name, since each is a write to
  Orca outside the host API.

## Approval

Anything that runs code needs an approval fingerprint (`ap1-…`). Orca's CLI
says the fingerprint is bound to the plugin, version, files and access, and
that a different set needs a new one. `dev load`, `enable` and the
documented `install` and `update` commands fail with `approval_required`
until re-run with `--approve <fingerprint>`.

Approving grants the access to that exact content. Ask the user before
passing `--approve`, unless they already approved this plugin, version and
access in so many words.

## Updates that skip approval

These are the silent update paths principle 6 of the shared skill asks
about:

- **Same-access updates keep approval.** The docs say an update from the
  same repository that asks for no new access keeps its approval, so new
  code under an unchanged manifest runs without a prompt.
- **Development folders rerun edits.** Orca reloads a development folder
  when its files change, and approved code edits run without asking again.
  Any `git pull` or checkout in that folder is an unreviewed update.
- **Git installs follow their ref.** The docs say a Git install pins the
  exact commit, but `plugin update` moves a version-tag install to the
  newest version tag and a branch install to its newest commit; only a
  commit pin stays.
- **Catalog installs follow their catalog.** The docs say a catalog decides
  which repositories Orca installs and auto-updates from. When Orca applies
  catalog updates without the user acting was not checked.

`orca plugin list --json` shows each plugin's `source` (`resolvedCommit`,
`contentHash`), `consentFingerprint`, `needsReconsent`, and for a
development folder `devChangeCount`. Compare them with the audited identity
after installing and before trusting a plugin again.

## Installing on the audited code

- **Orca 1.4.251 CLI:** it has no `plugin install` or `plugin update`. Clone
  the audited commit, detach `HEAD` at it, keep the checkout somewhere no
  update tool pulls, and run `orca plugin dev load <dir>`. The plugin loads
  as `local.<id>`, labelled `Dev · unverified`. Its updates are only what
  someone does to that checkout, so review any change there first.
- **Newer Orca or the GUI:** the docs describe
  `orca plugin install <owner/repo|git-url>` with `#<ref>` on a Git URL, and
  Settings → Plugins → Add plugin → From a Git URL. Give the full commit SHA
  as the ref so updates cannot move it. Avoid version tags, branches and
  catalog installs for unsandboxed plugins.

Record the source URL, commit, content hash and verdict where the next
audit will find it.

## Removing

`orca plugin dev unload <dir>` removes a development folder;
`orca plugin disable <key>` stops a plugin without removing it. The docs say
uninstalling never needs approval. Plugin storage and settings may outlive
removal: check before telling the user it is gone.

## Sources

- `docs/reference/plugin-authoring.md`, `plugin-manifest.md` and
  `plugin-catalog.md` in <https://github.com/stablyai/orca>
- `skill-guides/orca-cli/references/plugins.md` in the same repository
- `orca plugin <command> --help` in the installed Orca
