# Verdicts and reports

## Verdicts

Give exactly one verdict per candidate. Use the install wording for a plugin
that is not installed yet, and the upgrade wording otherwise.

- **Appears safe to install / upgrade:** the whole executable payload or
  delta was reviewed, behaviour matches its stated purpose, and no material
  concern remains.
- **Install / Upgrade with caution:** proceeding is still recommended, but a
  specific compatibility, migration, behavioural or bounded supply-chain risk
  needs a named prerequisite, check, or rollback trigger.
- **Do not install / upgrade:** a concrete security, integrity, destructive
  or serious regression concern exists. Explain the likely consequence for
  the user and a realistic trigger in plain language, not only the mechanism.
- **Inconclusive:** the executable or material dependency payload could not
  be reviewed well enough. Never promote it to safe on the strength of a
  changelog or reputation.

"With caution" is not a polite word for uncertainty. Attach one action to it:

- **Install / Upgrade now:** no blocker; name the post-change check and the
  symptom that would trigger rollback or removal.
- **Install / Upgrade after `<prerequisite>`:** name what must happen first,
  then the check and rollback symptom.
- **Defer until `<condition>`:** only for a specific current blocker, saying
  what evidence clears it.

If no concrete precaution can be named, the verdict is "appears safe". If the
risk cannot be bounded enough to name one, it is `Inconclusive`.

Keep the verdict on the code separate from exposure. A disabled or filtered
plugin is less exposed, but its update is no safer. Installing code may be
safe even when turning an optional feature on needs a controlled trial.

## Questions to answer before the verdict

1. Were all material runtime and instruction files reviewed?
2. Were install scripts, generated output, binaries and downloads resolved?
3. Were material dependency changes reviewed at the payload level?
4. Were the source, ref, identity and ancestry verified?
5. Was effective authority established and compared with declared
   authority?
6. Does the changelog match the code without hiding a material weakening?

If any of the first five is "no" and no decisive severe finding exists, the
verdict is `Inconclusive`.

## Report contents

Platform skills may set the format and location; every report still states:

- plugin name, platform identity and source URL;
- reviewed identity (commit SHA, version and integrity, or content hash), and
  for an update the previously approved identity;
- audit date and the platform version the behaviour was checked against;
- scope: files and dependencies covered, and anything opaque or not
  reviewed;
- execution surface: what runs, and what runs without user action;
- declared and effective authority, and the gap between them;
- sensitive behaviour found: processes, network, filesystem and secrets,
  writes to the host application, persistence;
- findings by severity, and anything unexplained;
- residual risks and limits of the review;
- how the install is pinned, and which update paths remain open;
- the verdict, and whether the user has approved.

## After approval

Record the approved identity, date and verdict where the next audit will look
for it, such as the platform skill's notes location or the repository's
research reports. Re-check after installing that the installed identity
matches the reviewed one.
