#!/usr/bin/env bash
#
# Emit one line per GitHub Actions job as it reaches a terminal state, then exit
# when the run completes. Written for the harness's Monitor tool: each stdout
# line becomes one notification.
#
# Usage: watch-run.sh <run-id> [--interval SECONDS] [--repo OWNER/REPO]

set -uo pipefail

interval=30
repo_args=()
run_id=""

while [ $# -gt 0 ]; do
    case "$1" in
        --interval)
            interval="$2"
            shift 2
            ;;
        --repo)
            repo_args=(--repo "$2")
            shift 2
            ;;
        -h | --help)
            sed -n '3,8p' "$0"
            exit 0
            ;;
        *)
            run_id="$1"
            shift
            ;;
    esac
done

if [ -z "$run_id" ]; then
    echo "watch-run.sh: no run ID given" >&2
    exit 64
fi

# Report every terminal conclusion, not just success: a monitor that greps for
# the happy path alone stays silent through a failure, and silence is
# indistinguishable from "still running".
finished_jobs() {
    gh run view "$run_id" "${repo_args[@]}" --json jobs \
        --jq '.jobs[] | select(.status == "completed") | "\(.name): \(.conclusion)"' \
        2>/dev/null | sort
}

run_state() {
    gh run view "$run_id" "${repo_args[@]}" --json status,conclusion \
        --jq '"\(.status)|\(.conclusion // "-")"' 2>/dev/null
}

previous=""
consecutive_failures=0

while true; do
    current="$(finished_jobs)"

    # A transient API error yields empty output; treating that as "no jobs have
    # finished" would re-announce every job once it recovers.
    if [ -z "$current" ] && [ -n "$previous" ]; then
        consecutive_failures=$((consecutive_failures + 1))
        if [ "$consecutive_failures" -ge 5 ]; then
            echo "WATCH ERROR: gh unreachable for $consecutive_failures polls; giving up"
            exit 69
        fi
        sleep "$interval"
        continue
    fi
    consecutive_failures=0

    comm -13 <(printf '%s\n' "$previous") <(printf '%s\n' "$current") 2>/dev/null \
        | grep -v '^$'
    previous="$current"

    state="$(run_state)"
    case "$state" in
        completed*)
            echo "RUN COMPLETE: ${state#*|}"
            exit 0
            ;;
    esac

    sleep "$interval"
done
