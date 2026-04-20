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

## Scope: Three Distinct Comment Surfaces

A GitHub PR carries feedback in three surfaces. All must be checked:

1. **Inline review threads** — attached to a line of code. These are the only
   ones with a real `isResolved` flag. Must be enumerated via GraphQL; REST
   does not expose resolution state.
2. **PR-level issue comments** — top-level comments on the Conversation tab.
   No resolution flag; treat as addressed when you've replied or acted.
3. **Review summary bodies** — the body of a submitted review (CodeRabbit
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

Replace the three `$...` placeholders with the literals from step 1:

```bash
mkdir -p tmp
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

### 3. Enumerate PR-level issue comments

```bash
gh api "repos/$OWNER/$REPO_NAME/issues/$PR_NUMBER/comments" --paginate \
  | tee tmp/issue-comments.json > /dev/null
```

### 4. Enumerate review summary bodies

```bash
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate \
  | tee tmp/reviews.json > /dev/null
```

Filter to reviews with a non-empty `body`. CodeRabbit and Copilot place their
actionable summary here.

### 5. Triage and address each item

For each unresolved thread / comment / review body:

1. **Read the content** and the code it refers to (use `path` and `line` from
   the thread, or parse file refs out of issue-comment / review bodies).
2. **Decide**: is the point valid, already addressed, out of scope, or wrong?
3. **Act**:
   - Valid & actionable → make the code change.
   - Already addressed in a later commit → note the commit SHA in the reply.
   - Out of scope → explain why and suggest a follow-up issue.
   - Wrong / disagree → explain the reasoning, don't just dismiss.
4. **Reply** (see step 6). Every item gets a reply explaining outcome.
5. **Resolve** if appropriate and possible (see step 7).

### 6. Post replies

**Inline thread reply** (preferred: GraphQL, using thread `id` from step 2):

```bash
gh api graphql -f query='
mutation($tid:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$tid, body:$body}) {
    comment { id url }
  }
}' -F tid="$THREAD_ID" -F body="$REPLY_BODY"
```

**PR-level issue comment reply** (no thread structure — just another comment):

```bash
gh pr comment "$PR_NUMBER" --body "$BODY"
```

Reference the comment you're replying to by quoting or linking its URL.

**Reply to a review summary**: post a PR-level issue comment quoting the
relevant section — GitHub has no "reply to review summary" primitive.

### 7. Resolve threads

Only resolve an inline thread when:
- `viewerCanResolve` is true, **and**
- The reply makes it clear the concern is addressed (fixed, invalid, or
  deferred with agreement).

Do NOT resolve threads where:
- The user might still want to weigh in.
- You disagree with the reviewer — let the human decide.
- The fix is speculative and unverified.

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

- **Thread `id` vs comment `databaseId`**: mutations use the opaque `id`.
  REST replies-to-comment use the numeric `databaseId` of the thread's first
  comment.
- **Outdated threads** (`isOutdated==true`): often the line moved/disappeared.
  Reply is still possible but may be low-value — use judgement.
- **Fork PRs from `GITHUB_TOKEN`** have read-only repo access; resolve
  mutations will fail. The user's `gh auth login` token is needed.
- **Pagination**: both REST endpoints need `--paginate`; the GraphQL query
  needs manual cursor handling if the PR has >100 threads.
- **No `isResolved` in REST**: don't try to filter unresolved via
  `/pulls/{pr}/comments` — it's not there.

## Output

After processing, summarise to the user:
- Count of threads/comments addressed, deferred, disagreed, resolved.
- Any that need the user's judgement before proceeding.
- Any code changes that still need committing & pushing.
