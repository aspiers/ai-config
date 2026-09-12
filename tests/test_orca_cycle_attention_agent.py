#!/usr/bin/env python3
"""
Test suite for the orca-cycle-attention-agent script.

Pins the ordering rules (blocked/waiting before done, newest first, stale or
interrupted completions dropped), the pane-to-terminal join, focused-pane
detection through nested layouts, and the exact `orca` CLI calls made.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import call, patch

BIN_DIR = Path(__file__).parents[1] / "bin"
SCRIPT = BIN_DIR / "orca-cycle-attention-agent"
SPEC = importlib.util.spec_from_loader(
    "orca_cycle_attention_agent",
    SourceFileLoader("orca_cycle_attention_agent", str(SCRIPT)),
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

NOW = 1_000_000_000
MINUTE = 60 * 1000


def agent(pane_key: str, state: str, started_ago_ms: int = 0, **extra):
    return {
        "paneKey": pane_key,
        "state": state,
        "stateStartedAt": NOW - started_ago_ms,
        **extra,
    }


def terminal(pane_key: str, handle: str, connected: bool = True):
    tab_id, leaf_id = pane_key.split(":")
    return {
        "handle": handle,
        "tabId": tab_id,
        "leafId": leaf_id,
        "connected": connected,
    }


class AttentionAgentsTests(unittest.TestCase):
    def test_orders_needs_input_before_done_and_newest_first(self) -> None:
        worktrees = [
            {
                "agents": [
                    agent("t1:l1", "working"),
                    agent("t2:l2", "done", started_ago_ms=5 * MINUTE),
                    agent("t3:l3", "waiting", started_ago_ms=20 * MINUTE),
                ]
            },
            {
                "agents": [
                    agent("t4:l4", "blocked", started_ago_ms=2 * MINUTE),
                    agent("t5:l5", "done", started_ago_ms=1 * MINUTE),
                    agent("t6:l6", "idle"),
                ]
            },
        ]

        self.assertEqual(
            [a["paneKey"] for a in MODULE.attention_agents(worktrees, NOW)],
            ["t4:l4", "t3:l3", "t5:l5", "t2:l2"],
        )

    def test_drops_stale_and_interrupted_completions_but_not_old_waits(self) -> None:
        worktrees = [
            {
                "agents": [
                    agent("stale", "done", started_ago_ms=MODULE.DONE_STALE_AFTER_MS + 1),
                    agent("interrupted", "done", interrupted=True),
                    agent("old-wait", "waiting", started_ago_ms=3 * 60 * MINUTE),
                    agent("fresh", "done", started_ago_ms=MODULE.DONE_STALE_AFTER_MS),
                ]
            }
        ]

        self.assertEqual(
            [a["paneKey"] for a in MODULE.attention_agents(worktrees, NOW)],
            ["old-wait", "fresh"],
        )


class PaneMappingTests(unittest.TestCase):
    def test_terminal_handles_skip_disconnected_terminals(self) -> None:
        handles = MODULE.terminal_handles(
            [terminal("t1:l1", "term_a"), terminal("t2:l2", "term_b", connected=False)]
        )

        self.assertEqual(handles, {"t1:l1": "term_a"})

    def test_focused_pane_keys_follow_active_worktree_through_splits(self) -> None:
        worktrees = [
            {"worktreeId": "wt-active", "isActive": True},
            {"worktreeId": "wt-other", "isActive": False},
        ]
        group = lambda tab, leaf, other_tab: {  # noqa: E731
            "type": "group",
            "activeTabId": tab,
            "tabs": [
                {"tabId": other_tab, "activeLeafId": "ignored"},
                {"tabId": tab, "activeLeafId": leaf},
            ],
        }
        layouts = [
            {
                "worktreeId": "wt-active",
                "root": {
                    "type": "split",
                    "first": group("t1", "l1", "t0"),
                    "second": group("t2", "l2", "t9"),
                },
            },
            {"worktreeId": "wt-other", "root": group("t3", "l3", "t8")},
        ]

        self.assertEqual(
            MODULE.focused_pane_keys(worktrees, layouts), {"t1:l1", "t2:l2"}
        )


class TargetAgentTests(unittest.TestCase):
    CANDIDATES = [
        {"paneKey": "first"},
        {"paneKey": "second"},
        {"paneKey": "third"},
    ]

    def test_starts_from_the_appropriate_end_when_nothing_is_focused(self) -> None:
        self.assertEqual(
            MODULE.target_agent(self.CANDIDATES, set(), "next")["paneKey"], "first"
        )
        self.assertEqual(
            MODULE.target_agent(self.CANDIDATES, set(), "previous")["paneKey"],
            "third",
        )

    def test_cycles_around_from_the_focused_candidate(self) -> None:
        self.assertEqual(
            MODULE.target_agent(self.CANDIDATES, {"third"}, "next")["paneKey"],
            "first",
        )
        self.assertEqual(
            MODULE.target_agent(self.CANDIDATES, {"first"}, "previous")["paneKey"],
            "third",
        )

    def test_returns_none_without_candidates(self) -> None:
        self.assertIsNone(MODULE.target_agent([], set(), "next"))


class CycleAttentionAgentTests(unittest.TestCase):
    def test_switches_to_the_target_terminal_through_the_cli(self) -> None:
        ps = {
            "worktrees": [
                {
                    "worktreeId": "wt",
                    "isActive": True,
                    "agents": [
                        agent("t1:l1", "done", started_ago_ms=MINUTE),
                        agent("t2:l2", "waiting"),
                        agent("gone:gone", "blocked"),
                    ],
                }
            ]
        }
        listing = {
            "terminals": [terminal("t1:l1", "term_done"), terminal("t2:l2", "term_wait")],
            "visualLayouts": [
                {
                    "worktreeId": "wt",
                    "root": {
                        "type": "group",
                        "activeTabId": "t2",
                        "tabs": [{"tabId": "t2", "activeLeafId": "l2"}],
                    },
                }
            ],
        }
        with patch.object(
            MODULE, "run_orca", side_effect=(ps, listing, {"focus": {}})
        ) as run:
            handle = MODULE.cycle_attention_agent("next", now_ms=NOW)

        self.assertEqual(handle, "term_done")
        self.assertEqual(
            run.call_args_list,
            [
                call(["worktree", "ps", "--limit", MODULE.LISTING_LIMIT]),
                call(
                    [
                        "terminal",
                        "list",
                        "--include-visual-layouts",
                        "--limit",
                        MODULE.LISTING_LIMIT,
                    ]
                ),
                call(["terminal", "switch", "--terminal", "term_done"]),
            ],
        )

    def test_does_nothing_when_no_agent_needs_attention(self) -> None:
        ps = {"worktrees": [{"worktreeId": "wt", "agents": [agent("t1:l1", "working")]}]}
        listing = {"terminals": [terminal("t1:l1", "term_a")], "visualLayouts": []}
        with patch.object(MODULE, "run_orca", side_effect=(ps, listing)) as run:
            self.assertIsNone(MODULE.cycle_attention_agent("next", now_ms=NOW))

        self.assertEqual(run.call_count, 2)


class RunOrcaTests(unittest.TestCase):
    def test_raises_on_error_envelope(self) -> None:
        completed = unittest.mock.Mock(
            stdout='{"ok": false, "error": {"code": "terminal_handle_stale"}}',
            stderr="",
            returncode=1,
        )
        with patch.object(MODULE.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "terminal_handle_stale"):
                MODULE.run_orca(["terminal", "switch", "--terminal", "x"])


if __name__ == "__main__":
    unittest.main()
