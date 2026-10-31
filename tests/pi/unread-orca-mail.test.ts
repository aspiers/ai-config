import assert from "node:assert/strict";
import test from "node:test";

import extension from "../../.pi/agent/extensions/unread-orca-mail.ts";

type Exec = (cmd: string, args: string[]) => Promise<{ code: number; stdout: string }>;

async function endTurn(exec: Exec, handle = "term_x") {
  const sent: unknown[][] = [];
  let onEnd: (() => Promise<void>) | undefined;
  const pi = {
    on: (event: string, handler: () => Promise<void>) => {
      if (event === "agent_end") onEnd = handler;
    },
    exec,
    sendMessage: (...args: unknown[]) => sent.push(args),
  };
  process.env.ORCA_TERMINAL_HANDLE = handle;
  if (!handle) delete process.env.ORCA_TERMINAL_HANDLE;
  extension(pi as never);
  await onEnd?.();
  return sent;
}

test("starts a follow-up turn listing unread mail", async () => {
  const sent = await endTurn(async (cmd, args) => {
    assert.deepEqual([cmd, args], ["ai-guard-orca-unread-mail", ["--text"]]);
    return { code: 0, stdout: "1 unread Orca message(s)\n" };
  });
  assert.deepEqual(sent, [[
    { customType: "orca-unread-mail", content: "1 unread Orca message(s)", display: true },
    { triggerTurn: true, deliverAs: "followUp" },
  ]]);
});

test("stays quiet with no unread mail", async () => {
  assert.deepEqual(await endTurn(async () => ({ code: 0, stdout: "" })), []);
});

test("stays quiet when the guard is missing", async () => {
  assert.deepEqual(await endTurn(async () => { throw new Error("ENOENT"); }), []);
});

test("does nothing outside Orca", async () => {
  const sent = await endTurn(async () => assert.fail("guard ran outside Orca"), "");
  assert.deepEqual(sent, []);
});
