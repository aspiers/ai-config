---
name: checking-upstream
description: >-
  Checks the canonical upstream issue tracker, discussion forums, and open
  pull requests, merge requests, or equivalent change queues for existing
  reports, discussion, or work on a problem just discussed. Use before
  diagnosing, fixing, or reporting an apparent open-source problem to avoid
  duplicate effort and missed context.
---

# Checking Upstream

Find existing upstream knowledge or work before taking action.

1. Infer the project and precise problem from the conversation and any command
   arguments. Ask one focused question only if either is unclear.
2. Identify the canonical upstream repository and tracker, not just a fork or
   package mirror.
3. Search the issue tracker, including closed issues, and the open pull
   request, merge request, patch, or equivalent change queue. Try a few
   focused variants: the exact error or symbol, the symptom, and the affected
   component.
4. Search the project's discussion venues too. Issues and change queues are
   never the whole record: feature requests, design debates, and "is this
   intended?" questions frequently live only in a forum, and a maintainer's
   answer there may be the sole statement of intent. Check every venue the
   project actually uses, for example:

   - GitHub Discussions, GitLab issue boards used as forums, or a Discourse
     instance;
   - a mailing list, Matrix/IRC/Discord/Slack archive, or wiki;
   - a `DISCUSSIONS.md`, `SUPPORT.md`, or README section naming where
     questions belong.

   Confirm which venues exist rather than assuming. On GitHub, Discussions
   are separate from issues and are missed by an issue-only search, so query
   them explicitly:

   ```bash
   gh api graphql -f query='
   {
     repository(owner: "OWNER", name: "REPO") {
       discussions(first: 1) { totalCount }
       discussionCategories(first: 20) { nodes { name } }
     }
   }'
   ```

   When the total is small (a few hundred or fewer), fetch title and body for
   all of them and filter locally — that is exhaustive and avoids missing a
   thread whose title never uses your search terms. Otherwise use
   `gh search` or the venue's own search with the same focused variants.
5. Read plausible matches enough to verify relevance. Note their status,
   latest meaningful activity, linked work, decisions, workarounds, and
   blockers.
6. Report concisely:
   - canonical upstream and tracker URLs;
   - which venues were searched, and which exist but were not searched;
   - relevant matches with title, status, URL, and why they match;
   - an assessment: active work, discussion only, previously resolved, or no
     relevant match;
   - any useful conclusions, workarounds, or missing information.

Prefer tracker-native search or APIs, with web search as a fallback. If no
matches are found, state the searches performed and the venues covered, and
note that this does not prove no report exists. Never report "not tracked
upstream" on the strength of an issue-only search; say which venues that
conclusion rests on.

Do not modify code, file or comment on an issue, or open a change request
unless explicitly asked.
