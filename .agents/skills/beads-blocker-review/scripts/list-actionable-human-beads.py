#!/usr/bin/env python3
"""Partition open human-labelled Beads issues by current readiness."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from json import JSONDecodeError
from typing import Any, Sequence


def read_issues(arguments: Sequence[str]) -> list[dict[str, Any]]:
    """Run a Beads JSON query and return its issue list."""
    resolved_bd_command = shutil.which("bd")
    if resolved_bd_command is None:
        raise RuntimeError("Beads command not found: bd")

    command = [resolved_bd_command, *arguments, "--json"]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or f"exit status {result.returncode}"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")

    try:
        issues = json.loads(result.stdout)
    except (JSONDecodeError,):
        raise RuntimeError(f"{' '.join(command)} returned invalid JSON") from None

    if not isinstance(issues, list) or not all(
        isinstance(issue, dict) and isinstance(issue.get("id"), str)
        for issue in issues
    ):
        raise RuntimeError(f"{' '.join(command)} returned an invalid issue list")

    return issues


def partition_human_issues(
    human_issues: Sequence[dict[str, Any]],
    ready_issues: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Split human-owned issues using Beads' authoritative ready result."""
    ready_ids = {issue["id"] for issue in ready_issues}
    actionable = [issue for issue in human_issues if issue["id"] in ready_ids]
    waiting = [issue for issue in human_issues if issue["id"] not in ready_ids]
    return {
        "counts": {
            "actionable": len(actionable),
            "waiting": len(waiting),
        },
        "actionable": actionable,
        "waiting": waiting,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List open human-labelled Beads issues, separating currently "
            "actionable questions from issues waiting on prerequisites."
        )
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit compact rather than indented JSON",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    human_issues = read_issues(["human", "list"])
    ready_issues = read_issues(
        ["ready", "--label=human", "--limit=0", "--brief"]
    )

    result = partition_human_issues(human_issues, ready_issues)
    indent = None if arguments.compact else 2
    print(json.dumps(result, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
