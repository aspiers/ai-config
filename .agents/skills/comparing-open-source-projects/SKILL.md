---
name: comparing-open-source-projects
description: >-
  Researches and compares free and open source software projects in a supplied
  domain, using either user-named candidates or a discovered shortlist. Use
  when evaluating FOSS alternatives, comparing GitHub popularity, maintenance,
  licences, domain fit, trade-offs, or producing a linked HTML comparison
  report.
---

# Comparing Open Source Projects

Compare projects against the user's actual domain and use case, not against a
context-free feature checklist. Treat current popularity, maintenance, and
licensing claims as evidence that must be checked rather than remembered.

## Establish the comparison set

- When the user names exact candidates, compare those candidates. Do not add or
  replace projects unless the user also asks for discovery.
- When the user supplies only a domain, define a transparent, representative
  shortlist from current research. Search across project websites, canonical
  forges, ecosystem directories, and credible roundups; then verify every
  candidate against primary sources.
- State the inclusion criteria and important exclusions. Do not imply that a
  shortlist is exhaustive.
- Ask one focused clarification when different interpretations of the domain
  would materially change the candidates or recommendation. Otherwise state
  reasonable assumptions in the report.
- If a named candidate is source-available, proprietary, abandoned, or not a
  real match, retain it and explain the limitation rather than silently
  substituting another project.

## Collect comparable evidence

Use the same observation date and activity window for every project. Prefer
canonical project and repository sources; use secondary sources to discover
claims, not to establish them.

For every candidate, establish:

1. **Identity and fit:** canonical project and repository, relevant edition or
   component, supported use cases, deployment model, and important scope
   boundaries.
2. **GitHub popularity:** the star count of the canonical primary repository,
   with its repository link and an as-of UTC date. Do not sum an organisation,
   plugins, forks, or mirrors. If GitHub is not canonical, report `N/A` and
   identify any GitHub mirror separately. Stars measure attention, not quality.
3. **Maintenance:** archived or deprecation state, date of the latest default-
   branch commit, latest stable release, commit/release activity over a common
   window, and evidence of issue or pull-request responsiveness where useful.
   Distinguish active development, maintenance-only maturity, sporadic work,
   inactivity, and insufficient evidence. Do not infer maintenance from stars
   or from one recent automated commit.
4. **Licence:** exact licence name and SPDX identifier when one exists, linked
   to the governing licence text. Check multiple licences, exceptions,
   component-specific terms, and community-versus-enterprise boundaries.
   GitHub's detected licence is a discovery hint, not a substitute for reading
   the repository's licence files. Clearly distinguish OSI/FSF-recognised open
   source licences from source-available terms and avoid presenting the report
   as legal advice.
5. **Decision factors:** capabilities relevant to the requested domain,
   maturity, integrations, operational burden, documentation/community, major
   limitations, and the kinds of users for whom the project is or is not a
   good fit.

Link factual claims to evidence. Use exact dates and counts where available,
and mark unknowns instead of estimating. Explain the basis of qualitative
maintenance ratings so a mature low-churn project is not automatically treated
as abandoned.

## Analyse and recommend

Normalise terminology and compare like with like. Separate observations from
judgement, identify material evidence gaps, and explain trade-offs instead of
manufacturing a universal winner. Base recommendations on the user's stated
needs and call out when licensing or maintenance makes an otherwise strong
candidate unsuitable.

## Produce the report

Read [the HTML reporting contract](references/reporting.md) completely before
writing the report. Use
[the self-contained report template](assets/report-template.html) as the
structural and visual basis. The finished report must be written under `tmp/`
in the current Git repository and opened with the repository-specific opener
described in the reporting contract.
