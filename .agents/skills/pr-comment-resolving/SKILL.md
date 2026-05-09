---
name: pr-comment-resolving
description: Find and address all unresolved GitHub PR review comments on the current branch's pull request. Use when the user asks to resolve, address, respond to, or reply to PR review feedback — whether from humans, CodeRabbit, Copilot, Claude Code reviewer, or any other source. Triggers on "/rr", "resolve review comments", "address PR feedback", "reply to review threads", "deal with CodeRabbit", etc.
---

# PR Comment Resolving

Find every unresolved review comment on the current branch's PR, try to address
each, reply explaining how it was addressed (or what blocks resolution), and
mark threads resolved where appropriate.

## When to Use This Skill

- `/rr` slash command
- User asks to resolve, address, or respond to PR review comments
- Working through feedback from CodeRabbit, Copilot, Claude Code reviewer, or human reviewers
- Cleaning up a PR before merge by closing out review threads

## Scope: Four Distinct Comment Surfaces

A GitHub PR carries feedback in four surfaces. **All must be checked** — and
**both the GraphQL and REST inline-comment endpoints must be queried**, because
they don't return the same set of items (see Gotchas).

1. **Inline review threads (GraphQL)** — attached to a line of code, grouped
   into threads. Only this view exposes the `isResolved` flag.
2. **Inline review comments (REST)** — the same general surface as #1, but
   the REST endpoint returns *every* review comment (including ungrouped
   ones some bots post that never appear as a GraphQL thread). **Always
   query both #1 and #2** and union by comment URL.
3. **PR-level issue comments** — top-level comments on the Conversation tab.
   No resolution flag; treat as addressed when you've replied or acted.
4. **Review summary bodies** — the body of a submitted review (CodeRabbit
   walkthrough, Copilot summary, human review comment). No resolution flag;
   often contain actionable items the inline threads don't cover.

## Input

The skill accepts an optional PR reference — a PR number (`123`), a full URL
(`https://github.com/owner/repo/pull/123`), or an `owner/repo#123` form. When
no argument is given, fall back to the current branch's PR.

## Process

### 1. Identify the PR

Parse the argument if provided:

- **URL** `https://github.com/OWNER/REPO/pull/N`: extract OWNER, REPO, N.
- **`OWNER/REPO#N`**: extract OWNER, REPO, N.
- **Bare number `N`**: use N with the current repo (from `gh repo view`).
- **No argument**: resolve from the current branch.

Resolve the PR once and read the identifiers into your own context. Review
threads live on the **base** repo (not the head repo — important for
cross-fork PRs), so use `baseRepository`:

```bash
# Pass the PR ref if given (number, URL, or branch). Omit to use current branch.
gh pr view [PR_REF] --json number,baseRepository \
  -q '{num:.number, owner:.baseRepository.owner.login, repo:.baseRepository.name}'
```

Example output: `{"num":42,"owner":"adamspiers-org","repo":"ai-config"}`.

For `owner/repo#N` input, split into `OWNER/REPO` and `N` and pass them as
`gh -R OWNER/REPO pr view N`.

**Do not persist these values to disk.** Shell state is not preserved between
`Bash` tool calls, and any file-based approach breaks when multiple agents
share a worktree. Instead, read the three values from the JSON output above
and **substitute the literals directly into every subsequent command** in
steps 2-7. For example, once you have `num=42, owner=foo, repo=bar`, the
step 3 command becomes:

```bash
gh api "repos/foo/bar/issues/42/comments" --paginate \
  | tee tmp/issue-comments.json > /dev/null
```

— no variables, no sourcing. The commands below use `$OWNER`, `$REPO_NAME`,
`$PR_NUMBER` as **placeholders for you to replace**, not as shell variables.

If `gh pr view` fails with "no pull requests found" (and no argument was
given), stop and report — no PR exists for the current branch. If a bad
argument was given, show the error and stop.

### 2. Enumerate unresolved inline review threads (GraphQL)

Write the query to `tmp/unresolved-threads.json` for repeated analysis without
re-fetching (per the user's preference for capturing gh output via tee).

**Always wipe stale tmp files first.** Earlier `/rr` runs against other PRs
may have left `tmp/review-threads.json` etc. on disk. If your shell has
`noclobber` set (zsh defaults to it under some configs), `>` redirects
silently fail when the target exists, leaving the *old* file's contents in
place — which means you'll triage threads belonging to a *different PR*
without realising it. Defence: explicitly delete first.

Stick to the `tee` form below (it overwrites unconditionally); never
substitute `> tmp/foo.json` because `>` interacts badly with `noclobber`.

Replace the three `$...` placeholders with the literals from step 1:

```bash
mkdir -p tmp
rm -f tmp/review-threads.json tmp/unresolved-threads.json \
      tmp/pull-comments.json tmp/issue-comments.json tmp/reviews.json
gh api graphql -f query='
query($owner:String!, $repo:String!, $pr:Int!, $cursor:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$pr) {
      reviewThreads(first:100, after:$cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          isCollapsed
          path
          line
          viewerCanResolve
          viewerCanReply
          comments(first:50) {
            nodes {
              id
              databaseId
              body
              url
              createdAt
              author { login __typename }
              replyTo { id }
            }
          }
        }
      }
    }
  }
}' -F owner="$OWNER" -F repo="$REPO_NAME" -F pr="$PR_NUMBER" \
  | tee tmp/review-threads.json \
  | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)]' \
  > tmp/unresolved-threads.json
```

Paginate if `.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage` is
true — re-run with `-F cursor="$END_CURSOR"` and merge.

### 3. Enumerate inline review comments (REST) — REQUIRED cross-check

GraphQL `reviewThreads` does **not** return every inline review comment. In
particular, recent Copilot reviews often surface inline comments via REST
that never appear in `reviewThreads` (no thread wrapper). Always also fetch:

```bash
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  | tee tmp/pull-comments.json > /dev/null
```

Then cross-check: any comment URL in `tmp/pull-comments.json` that isn't
covered by a thread in `tmp/review-threads.json` is an **orphan inline
comment** that the GraphQL query missed. Treat them like inline review
threads (same triage / reply rules) — but reply via the REST
*reply-to-review-comment* endpoint (step 6) rather than the GraphQL
thread-reply mutation, since they have no thread `id`.

```bash
# Build a quick sanity check: how many inline comments did each surface return?
echo "GraphQL threads: $(jq '.data.repository.pullRequest.reviewThreads.nodes | length' tmp/review-threads.json)"
echo "REST inline comments: $(jq 'length' tmp/pull-comments.json)"
```

Mismatches between the two are normal — REST counts individual comments
across reviews; GraphQL counts thread groupings. The check fails if **REST
returns inline comments whose URLs don't appear inside any GraphQL thread's
nested comments** — those are the ones GraphQL silently dropped.

### 4. Enumerate PR-level issue comments

```bash
gh api "repos/$OWNER/$REPO_NAME/issues/$PR_NUMBER/comments" --paginate \
  | tee tmp/issue-comments.json > /dev/null
```

### 5. Enumerate review summary bodies

```bash
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate \
  | tee tmp/reviews.json > /dev/null
```

Filter to reviews with a non-empty `body`. CodeRabbit and Copilot place their
actionable summary here.

### 6. Triage and address each item

For each unresolved thread / orphan REST inline comment / PR-level comment /
review body:

1. **Read the content** and the code it refers to (use `path` and `line` from
   the thread or REST comment, or parse file refs out of issue-comment /
   review bodies).
2. **Decide**: is the point valid, already addressed, out of scope, or wrong?
3. **Act**:
   - Valid & actionable → make the code change.
   - Already addressed in a later commit → note the commit SHA in the reply.
   - Out of scope → explain why and suggest a follow-up issue.
   - Wrong / disagree → explain the reasoning, don't just dismiss.
4. **Reply** (see step 7). Every item gets a reply explaining outcome.
5. **Resolve** if appropriate and possible (see step 8).

### 7. Post replies

Always include short sentence at the top of the reply making it clear that
this reply has been posted by an AI agent, e.g.

```markdown
_(reply generated by <INSERT NAME OF AGENT / LLM HERE>)_
```

**Inline thread reply** (when a GraphQL `id` exists from step 2 — preferred
because it groups under the original thread):

```bash
gh api graphql -f query='
mutation($tid:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$tid, body:$body}) {
    comment { id url }
  }
}' -F tid="$THREAD_ID" -F body="$REPLY_BODY"
```

**Orphan inline review comment reply** (REST — for comments found in step 3
that have no matching GraphQL thread). Use the **numeric `id` of the
original review comment** as `$COMMENT_ID`:

```bash
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -f body="$REPLY_BODY"
```

This creates a new review comment on the same PR review that threads
visually under the original — same UX as a GraphQL thread reply, just via
the only API surface available for these orphans.

**PR-level issue comment reply** (no thread structure — just another comment):

```bash
gh pr comment "$PR_NUMBER" --body "$BODY"
```

Reference the comment you're replying to by quoting or linking its URL.

**Reply to a review summary**: post a PR-level issue comment quoting the
relevant section — GitHub has no "reply to review summary" primitive.

### 8. Resolve threads

**Default to resolving** when the reply is a "Fixed in `<sha>`" or "Already
addressed in `<sha>`" closeout — leaving these open clutters the PR and
forces the user to do another pass. The user can always re-open if they
disagree with the fix.

Resolve when:
- `viewerCanResolve` is true, **and**
- The reply is a fix, an "already addressed", or a deferred-with-agreement
  closeout. Bot reviewer (Copilot, CodeRabbit) comments where you've
  applied their suggestion are the canonical case.

Do NOT resolve when:
- **You disagreed with the reviewer** — let the human decide whether the
  disagreement holds. The unresolved state is the signal that human review
  is wanted.
- The fix is speculative or unverified.
- The reply is "Out of scope, see #N" pointing at a different PR — that's
  a redirect, not a closeout. Let the human decide whether to dismiss.

**When you deliberately leave a thread unresolved, the reply MUST end with
a sentence explaining why** — so reviewers and the user don't have to
guess whether resolution was forgotten or intentional. Be specific about
what's needed to close it. Examples:

- "Leaving this thread open until @<reviewer> weighs in on the disagreement
  above."
- "Leaving open — the suggested approach changes public API shape, so I
  want a maintainer to confirm before resolving."
- "Leaving open for human judgement: the fix touches code outside this
  PR's scope (see #N) and the reviewer hasn't confirmed whether to defer."

A thread reply with no resolution rationale reads as accidentally
abandoned. Make the intent explicit.

```bash
gh api graphql -f query='
mutation($tid:ID!) {
  resolveReviewThread(input:{threadId:$tid}) {
    thread { id isResolved }
  }
}' -F tid="$THREAD_ID"
```

## Identifying Comment Sources

In the GraphQL response, `author.__typename` is `"Bot"` or `"User"`. Known bots:

| Source | Login (GraphQL) | Login (REST) |
|--------|-----------------|--------------|
| CodeRabbit | `coderabbitai` | `coderabbitai[bot]` |
| Copilot reviewer | `copilot-pull-request-reviewer` | `copilot-pull-request-reviewer[bot]` |
| GitHub Actions | `github-actions` | `github-actions[bot]` |
| Claude Code reviewer | varies (`claude[bot]` for official app; PAT user for self-hosted) | varies |

Treat bot comments with the same rigor as human ones — CodeRabbit in
particular surfaces real issues.

## Reply Style

Each reply should be one of:

- **Fixed**: "Fixed in `<sha>`. `<one-line explanation>`."
- **Already addressed**: "Addressed earlier in `<sha>` — `<brief>`."
- **Deferred**: "Out of scope for this PR. Filed as `<issue link or note>`."
- **Disagreed**: "`<reasoning>`. Leaving as-is."

Keep replies terse. Link to commits / issues rather than restating changes.

## Gotchas

- **Stale `tmp/*.json` from earlier runs**. If you ran `/rr` against
  another PR previously, `tmp/review-threads.json` already exists. With
  `noclobber` enabled in your shell (zsh frequently has it), `>` silently
  fails to overwrite, and `jq` then reads the old file — making you
  triage *another PR's* threads. The fix in step 2 (`rm -f tmp/*.json`)
  prevents this. Cross-check: every thread URL should start with the
  current PR number; if a sibling number appears (e.g. you're on #718
  but URLs say `#672`), the file is stale.
- **GraphQL `reviewThreads` is occasionally undercounted vs REST.**
  Recent Copilot reviews sometimes have a window where their inline
  comments appear in REST `/pulls/{pr}/comments` but not yet in GraphQL
  `reviewThreads` (likely an indexing delay; tested confirming a *single*
  comment does materialise as a thread immediately under normal
  conditions). **Always query both endpoints and union by comment URL.**
  If counts disagree, trust REST and reply via the REST replies
  endpoint. The GraphQL thread `id` will appear shortly after for
  resolution.
- **Thread `id` vs comment `databaseId`**: GraphQL `addPullRequestReviewThreadReply`
  takes the opaque thread `id`. REST `/comments/{id}/replies` takes the
  numeric review-comment `id` (`.id` on a `pull-comments.json` entry, NOT
  `databaseId`).
- **Outdated threads** (`isOutdated==true`): often the line moved/disappeared.
  Reply is still possible but may be low-value — use judgement.
- **Cross-PR thread reuse**: GitHub may surface review threads from earlier
  PRs that touched the same files. Check `comments[0].url` — if it points
  to a different PR number, the thread isn't really on this PR. Don't
  reply (it'd appear on the other PR); flag in the summary instead.
- **Fork PRs from `GITHUB_TOKEN`** have read-only repo access; resolve
  mutations will fail. The user's `gh auth login` token is needed.
- **Pagination**: both REST endpoints need `--paginate`; the GraphQL query
  needs manual cursor handling if the PR has >100 threads.
- **No `isResolved` in REST**: don't try to filter unresolved via
  `/pulls/{pr}/comments` — it's not there. The orphan-REST-only comments
  also have no resolution state at all; treat "I replied" as the
  closeout signal.

## Output

After processing, summarise to the user:
- Count of threads/comments addressed, deferred, disagreed, resolved.
- Any that need the user's judgement before proceeding.
- Any code changes that still need committing & pushing.
