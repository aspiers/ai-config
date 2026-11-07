# Security audit: rolottr/orca-collapse (Auto Collapse for Orca)

Audited 2026-11-07 at commit `3fff7030b7b337ff2a645ce92414b46083f18ebd`
(tag `v1.0.0`, the repository's only commit). Orca content hash for that
tree: `ffb406f13975e1e410f7e59e496b7f966d6f843c653a208a474fad4ac1fd31d8`.

## Verdict

Safe at this commit. The risk is future versions: the plugin runs with far
more power than its declared capabilities suggest, so any update needs the
same review before it runs.

## What the code does

The repository has one code file, `main.mjs` (227 lines), plus tests, a
manifest, images and a README. There is no `package.json` and nothing is
installed from npm.

- It imports only `node:fs`, `node:net`, `node:os` and `node:path`. There is
  no `child_process`, `fetch`, `http`, `eval`, `Function()` or dynamic
  `import()`.
- On `workspace.changed` and `agent.status.changed` it reads Orca's
  `orca-runtime.json` from the Orca data folder, takes the local socket
  endpoint and auth token, and calls four runtime methods over that socket:
  `ui.get`, `worktree.ps`, `projectHostSetup.list` and
  `ui.set { collapsedGroups }`.
- The only write is the list of collapsed sidebar groups. It re-reads the
  list just before writing, so a toggle made in the meantime survives.
- The token goes only to the socket named in the same metadata file. Nothing
  leaves the machine.
- Its own storage holds the last state of each sidebar section.
- The images are what `file` says they are: a PNG icon, a WebP cover and an
  animated WebP demo.

The README's claims ("sends nothing over the network and collects no data")
match the code at this commit.

## The real risk: hidden authority

- **Execution profile.** The manifest declares `trusted-worker`. Orca's own
  approval text says this "runs its own code in a separate Node.js process on
  the Orca host, with your user account's access to that machine". Any
  trusted worker can read your files and open network connections, whatever
  capabilities it lists.
- **Runtime token.** The plugin uses the same runtime token as the `orca`
  CLI, bypassing the plugin host API. Whether Orca scopes that token was not
  checked; if it doesn't, the plugin can do anything the CLI can, including
  sending text to terminals and launching agents. None of that shows up in
  the declared capabilities (`workspace:read`, `agent:read`, `storage:own`,
  `settings:own`).
- **Updates.** Orca's documentation says an update from the same repository
  that asks for no new access keeps its approval. A later version could keep
  the same manifest and run different code without a new prompt. The same
  holds for a development folder: Orca reruns edited code without asking.
- **Provenance.** The repository was created on 2026-11-03 with no stars or
  forks; the owner's GitHub account dates from 2021. That says nothing bad,
  but no one else has vetted it.

## Installing it safely

Pin the reviewed commit and make sure nothing can move it:

- Install from a checkout held at the reviewed commit (detached HEAD) that
  no update tool pulls, and load it with `orca plugin dev load <dir>`.
  Orca 1.4.251's CLI has no `plugin install` or `plugin update`, so this is
  the CLI route there.
- Or install from the Git URL in Settings → Plugins with the commit as the
  ref. Orca's docs say Git installs pin the exact commit, and that a commit
  pin stays put on update. Installing from a version tag or a catalog lets
  updates move to new code.
- Before moving to a newer version, diff it against
  `3fff7030b7b337ff2a645ce92414b46083f18ebd` and repeat this review.

## Non-security notes

- The plugin depends on Orca's internal runtime socket protocol and the
  `collapsedGroups` key, not on the plugin host API, so an Orca update could
  break it without warning.
- Its tests (`main.test.mjs`) cover only the planning functions, not the
  socket code. They were not run for this audit.

## Sources

- Plugin repository: <https://github.com/rolottr/orca-collapse>
- Orca plugin docs: `docs/reference/plugin-authoring.md`,
  `plugin-manifest.md` and `plugin-catalog.md`, and
  `skill-guides/orca-cli/references/plugins.md`, in
  <https://github.com/stablyai/orca> (main branch, read 2026-11-07)
- `orca plugin inspect` and `orca plugin dev load` output from Orca 1.4.251
