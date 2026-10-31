// opencode counterpart of the ai-guard-orca-unread-mail Claude Code Stop
// hook. When a session goes idle inside an Orca terminal with orchestration
// mail it has not read, prompt it again listing that mail. The guard raises
// each message once, so this cannot loop.

const GUARD = "ai-guard-orca-unread-mail";

async function unreadReason(path) {
  const proc = Bun.spawn([path, "--text"], { stdout: "pipe", stderr: "pipe" });
  const [code, out] = await Promise.all([
    proc.exited,
    new Response(proc.stdout).text(),
  ]);
  return code === 0 ? out.trim() : "";
}

export const OrcaUnreadMail = async ({ client }) => {
  const path = Bun.which(GUARD, { PATH: process.env.PATH });
  if (!path || !process.env.ORCA_TERMINAL_HANDLE) return {};

  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") return;
      const sessionID = event.properties?.sessionID;
      if (!sessionID) return;
      const reason = await unreadReason(path);
      if (!reason) return;
      await client.session.prompt({
        path: { id: sessionID },
        body: { parts: [{ type: "text", text: reason }] },
      });
    },
  };
};
