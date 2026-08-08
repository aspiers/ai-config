---
name: submitting-upstream
description: >-
  Prepare and publish upstream issues, feature requests, discussions, pull or
  merge requests, and patch submissions in the channel the canonical project
  expects. Use when reporting a problem upstream, requesting a feature,
  contributing a change, or asking to submit upstream.
---

# Submitting Upstream

Prepare the kind of upstream submission the user requested. Do not assume
that "submit upstream" means a code change: an issue, feature request, or
discussion needs no branch or commits.

## Choose the submission type

Infer the intended artefact from the request and current context:

- A problem report, feature request, or proposed behaviour normally becomes an
  issue.
- An idea the project explicitly routes to a forum becomes a discussion or
  proposal.
- An implemented local change normally becomes a pull request, merge request,
  or patch series.
- Documentation, security, and support requests may have dedicated channels.

If more than one type is plausible and the choice affects the work, ask one
focused question before preparing anything.

## Find the canonical destination

Identify the canonical project and its actual submission channel rather than
a fork, package mirror, or downstream tracker. Check repository metadata,
project documentation, release activity, and tracker activity when ownership
is not obvious.

Use the `checking-upstream` skill before drafting. Read plausible matches,
including closed reports and the open change queue. Existing work, a prior
resolution, or an explicit rejection may make a new submission unnecessary or
change it into a comment on an existing thread.

## Read the relevant rules

Look for the guidance that applies to the selected submission type. Do not
make code-contribution ceremony a prerequisite for filing an issue.

For any submission, check as applicable:

- issue, discussion, pull-request, or merge-request templates;
- `CONTRIBUTING*`, support and security policies, and project website
  guidance;
- required tracker fields, categories, labels, reproduction details, or prior
  discussion;
- codes of conduct and rules against disclosing sensitive data.

For code contributions, also inspect:

- target-branch and fork policy;
- DCO, CLA, sign-off, and copyright requirements;
- commit-message and history conventions;
- formatting, lint, test, build, changelog, and generated-file requirements;
- CI workflows and a few recent merged changes when written guidance is
  silent.

Treat documented rules as authoritative. If observed practice conflicts with
them, report the conflict instead of silently choosing one.

## Prepare the submission

### Issues, feature requests, and discussions

No branch or commit is needed.

Follow the project's template and preserve its headings. When there is no
template, draft a concise title and a body containing the useful subset of:

- the problem or requested capability;
- current and expected behaviour;
- reproduction steps and environment for a bug;
- motivation and concrete use cases for a feature;
- relevant logs, screenshots, or minimal examples;
- related issues and the upstream search already performed;
- known workarounds or implementation facts, clearly separated from the
  requested outcome.

State evidence precisely and remove secrets, personal data, private URLs, and
unrelated local details. Do not invent labels, severity, maintainer decisions,
or implementation requirements that the project has not established.

### Code changes

Only use this path when code is actually being contributed.

1. Fetch the canonical upstream and branch from its required, freshly fetched
   target branch.
2. Port only the relevant change; exclude personal configuration, debug
   output, secrets, and unrelated formatting churn.
3. Shape commits to the project's documented or observed conventions. Never
   add another person's sign-off or claim a CLA on their behalf.
4. Add required tests, documentation, changelog entries, and generated files.
5. Run the project's verification commands and distinguish introduced failures
   from pre-existing or environmental ones.
6. Draft the pull request, merge request, or patch text using the project's
   template and requested linkage syntax.

If a required rule is unmet, state it plainly and fix it before presenting
the submission as ready. Legal attestations such as DCO sign-off and CLA
acceptance cannot be waived or fabricated.

## Approval boundary

Creating an issue or discussion, commenting publicly, pushing a branch,
opening a change request, or sending patches is outward-facing. Prepare the
exact title and body, patch, or branch first, then stop for explicit approval
before the first publication action.

Present:

- the canonical destination and chosen submission type;
- relevant guidance and whether each requirement is satisfied;
- existing upstream work and how this submission relates to it;
- the exact draft;
- for code, the base, commits, diff scope, and verification results;
- the command or action that will publish it.

Once the user approves that prepared artefact, perform only the approved
publication action and return its URL or delivery result. Do not turn approval
to file an issue into permission to push code, or approval to push a branch
into permission to open a change request.

After a code submission, use the `pr-comment-resolving` skill for review
feedback and `watching-ci-runs` when CI results determine the next step.
