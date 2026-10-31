import { afterAll, expect, test } from "bun:test";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { OrcaUnreadMail } from "../../.config/opencode/plugins/unread-orca-mail.js";

const dir = mkdtempSync(join(tmpdir(), "unread-orca-mail-"));
afterAll(() => rmSync(dir, { recursive: true }));

async function idle(output) {
  const guard = join(dir, "ai-guard-orca-unread-mail");
  writeFileSync(guard, `#!/bin/sh\nprintf '%s' '${output}'\n`);
  chmodSync(guard, 0o755);
  process.env.PATH = `${dir}:${process.env.PATH}`;
  process.env.ORCA_TERMINAL_HANDLE = "term_x";
  const prompts = [];
  const client = { session: { prompt: async (request) => prompts.push(request) } };
  const hooks = await OrcaUnreadMail({ client });
  await hooks.event({ event: { type: "session.idle", properties: { sessionID: "ses_1" } } });
  return prompts;
}

test("prompts the idle session with the unread mail", async () => {
  expect(await idle("1 unread Orca message(s)")).toEqual([
    { path: { id: "ses_1" }, body: { parts: [{ type: "text", text: "1 unread Orca message(s)" }] } },
  ]);
});

test("stays quiet with no unread mail", async () => {
  expect(await idle("")).toEqual([]);
});
