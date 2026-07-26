---
name: checking-upstream
description: >-
  Checks the canonical upstream issue tracker and open pull requests, merge
  requests, or equivalent change queues for existing reports, discussion, or
  work on a problem just discussed. Use before diagnosing, fixing, or
  reporting an apparent open-source problem to avoid duplicate effort and
  missed context.
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
4. Read plausible matches enough to verify relevance. Note their status,
   latest meaningful activity, linked work, decisions, workarounds, and
   blockers.
5. Report concisely:
   - canonical upstream and tracker URLs;
   - relevant matches with title, status, URL, and why they match;
   - an assessment: active work, discussion only, previously resolved, or no
     relevant match;
   - any useful conclusions, workarounds, or missing information.

Prefer tracker-native search or APIs, with web search as a fallback. If no
matches are found, state the searches performed and note that this does not
prove no report exists.

Do not modify code, file or comment on an issue, or open a change request
unless explicitly asked.
