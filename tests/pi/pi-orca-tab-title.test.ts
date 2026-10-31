import assert from "node:assert/strict";
import test from "node:test";

import type { SessionEntry } from "@earendil-works/pi-coding-agent";

import {
  orcaTerminalHandle,
  resolveOrcaTitle,
} from "../../.pi/agent/extensions/pi-orca-tab-title.ts";

const info = { type: "session_info" } as SessionEntry;
const names = (data: object) =>
  ({ type: "custom", customType: "pi-tmux-window-name/window", data }) as SessionEntry;

test("uses the generated short name", () => {
  assert.equal(
    resolveOrcaTitle([info, names({ windowName: "Tabs", shortName: "Orca tab titles" })], "Long"),
    "Orca tab titles",
  );
});

test("a later /name wins over the generated short name", () => {
  assert.equal(
    resolveOrcaTitle([info, names({ windowName: "Tabs", shortName: "Orca tab titles" }), info], "Manual"),
    "Manual",
  );
});

test("falls back to the session name without a short name", () => {
  assert.equal(resolveOrcaTitle([info, names({ windowName: "Tabs" })], "Long name"), "Long name");
  assert.equal(resolveOrcaTitle([], "Long name"), "Long name");
});

test("only owns the tab outside Herdr and tmux", () => {
  assert.equal(orcaTerminalHandle({ ORCA_TERMINAL_HANDLE: "term_1" }), "term_1");
  assert.equal(orcaTerminalHandle({ ORCA_TERMINAL_HANDLE: "term_1", TMUX: "/s,1,0" }), undefined);
  assert.equal(orcaTerminalHandle({ ORCA_TERMINAL_HANDLE: "term_1", HERDR_ENV: "1" }), undefined);
  assert.equal(orcaTerminalHandle({}), undefined);
});
