#!/usr/bin/env bash
#
# Survey every open PR and report which are actually mergeable.
#
# Two passes: a cheap inventory of all open PRs, then per-PR checks and
# review-thread state for the shortlist only. The shortlist is the point —
# querying checks for a draft or a conflicted PR wastes an API round trip
# to tell you something the inventory already said.
#
# Usage: pr-triage.sh [-R owner/repo] [-l limit] [-a]
#   -R  repository (default: the one for $PWD)
#   -l  max PRs to inventory (default 100; gh's own default is far lower
#       and silently truncates)
#   -a  also run per-PR checks on drafts and conflicted PRs

set -uo pipefail

REPO=""
LIMIT=100
ALL=0

while getopts 'R:l:ah' opt; do
  case "$opt" in
    R) REPO="$OPTARG" ;;
    l) LIMIT="$OPTARG" ;;
    a) ALL=1 ;;
    h|?) sed -n '3,14p' "$0" | sed 's/^# \?//'; exit 0 ;;
  esac
done

if [ -z "$REPO" ]; then
  REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner) || exit 1
fi
OWNER=${REPO%%/*}
NAME=${REPO##*/}

# Written rather than piped so the inventory can be re-read for the
# shortlist without a second API call. mktemp avoids zsh noclobber
# silently refusing to overwrite a stale file from an earlier run.
inventory=$(mktemp) || exit 1
trap 'rm -f "$inventory"' EXIT

gh pr list --repo "$REPO" --state open --limit "$LIMIT" \
  --json number,title,isDraft,mergeable,mergeStateStatus,additions,deletions,changedFiles \
  > "$inventory" || exit 1

total=$(jq length "$inventory")
printf '%s: %s open PRs\n\n' "$REPO" "$total"

jq -r '.[] | [
    (.number|tostring),
    (if .isDraft then "draft" else "ready" end),
    .mergeable, .mergeStateStatus,
    ("+"+(.additions|tostring)+"/-"+(.deletions|tostring)),
    ((.changedFiles|tostring)+"f"),
    .title
  ] | @tsv' "$inventory" | column -t -s "$(printf '\t')"

# Non-draft and conflict-free. MERGEABLE with mergeStateStatus BLOCKED is
# the normal state for a healthy PR under a ruleset that requires review —
# BLOCKED alone is not a reason to exclude. UNKNOWN means GitHub is still
# recomputing after another merge, so it is included and flagged rather
# than dropped.
if [ "$ALL" -eq 1 ]; then
  shortlist=$(jq -r '.[].number' "$inventory")
else
  shortlist=$(jq -r '.[] | select(.isDraft|not)
                        | select(.mergeable != "CONFLICTING")
                        | .number' "$inventory")
fi

if [ -z "$shortlist" ]; then
  printf '\nNo non-draft, conflict-free PRs.\n'
  exit 0
fi

printf '\n--- checks and review threads ---\n'

for n in $shortlist; do
  title=$(jq -r --argjson n "$n" '.[]|select(.number==$n)|.title' "$inventory")
  state=$(jq -r --argjson n "$n" '.[]|select(.number==$n)|.mergeable+"/"+.mergeStateStatus' "$inventory")
  printf '\n#%s  %s\n  %s\n' "$n" "$state" "$title"

  # Report only what is NOT passing, so a clean PR costs one line rather
  # than twenty. "skipping" is normal here: deploy-gated jobs stay
  # permanently skipped on PRs and are not failures.
  gh pr checks "$n" --repo "$REPO" --json name,bucket --jq '
    [.[] | select(.bucket != "pass" and .bucket != "skipping")]
    | if length == 0 then "  checks: all green"
      else (.[] | "  checks: " + (.bucket|ascii_upcase) + " " + .name) end' \
    2>/dev/null || printf '  checks: (none reported)\n'

  # Only GraphQL exposes isResolved; the REST review-comments endpoint
  # has no resolution state at all.
  gh api graphql -f query='
    query($owner:String!,$repo:String!,$n:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$n){
          reviewThreads(first:100){
            nodes{ isResolved isOutdated path
                   comments(first:1){nodes{author{login}}} } } } } }' \
    -F owner="$OWNER" -F repo="$NAME" -F n="$n" --jq '
      .data.repository.pullRequest.reviewThreads.nodes
      | map(select(.isResolved == false))
      | if length == 0 then "  threads: none unresolved"
        else "  threads: " + (length|tostring) + " unresolved ("
             + ([.[] | (.comments.nodes[0].author.login // "?")
                       + (if .isOutdated then " outdated" else "" end)]
                | join(", ")) + ")" end' \
    2>/dev/null || printf '  threads: (query failed)\n'
done

# Why a healthy PR still says BLOCKED. Queried once, not per PR — it is a
# property of the branch, and printing it per PR would bury the shortlist.
printf '\n--- branch ruleset ---\n'
gh api "repos/$REPO/rulesets" --jq '.[].id' 2>/dev/null | while read -r id; do
  gh api "repos/$REPO/rulesets/$id" --jq '
    "\(.name) [\(.target), \(.enforcement)]",
    ( .rules[]
      | select(.type == "pull_request" or .type == "required_status_checks")
      | if .type == "pull_request" then
          "  approvals required: \(.parameters.required_approving_review_count)"
          + "   thread resolution: \(.parameters.required_review_thread_resolution)"
        else
          "  required checks: "
          + ([.parameters.required_status_checks[].context] | join(", "))
        end )' 2>/dev/null
done
