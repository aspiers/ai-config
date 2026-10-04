// opencode plugin adapter for command guards written as Claude Code
// PreToolUse hooks: dcg (Destructive Command Guard) and this repository's
// ai-guard-git-worktree-add.
//
// Claude Code's hook protocol natively pipes JSON to a subprocess's stdin
// and interprets JSON responses. opencode's plugin system is purely
// in-process JS, so this plugin bridges the gap by doing the
// spawn/pipe/parse manually.
//
// Protocol: send {"tool_name", "tool_input"} on stdin. A guard writes
// nothing on stdout for allowed commands, or a JSON object with
// hookSpecificOutput.permissionDecision === "deny" for blocked ones.

const GUARDS = [
  { command: "dcg", env: { DCG_ROBOT: "1" } },
  { command: "ai-guard-git-worktree-add", env: {} },
];

async function denyReason(path, env, payload) {
  const proc = Bun.spawn([path], {
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
    env: { ...process.env, ...env },
  });
  proc.stdin.write(payload);
  proc.stdin.end();
  const [, out] = await Promise.all([
    proc.exited,
    new Response(proc.stdout).text(),
  ]);
  // Empty stdout means the guard allowed the command
  const last = out.trimEnd().split("\n").pop();
  if (!last) return null;
  const result = JSON.parse(last);
  if (result?.hookSpecificOutput?.permissionDecision !== "deny") return null;
  return result.hookSpecificOutput.permissionDecisionReason ?? `blocked by ${path}`;
}

export const PreToolUseGuards = async () => {
  const guards = GUARDS.map((g) => ({ ...g, path: Bun.which(g.command) })).filter(
    (g) => g.path,
  );
  if (guards.length === 0) return {};

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const payload = JSON.stringify({
        tool_name: "Bash",
        tool_input: { command: output.args.command },
      });
      for (const guard of guards) {
        const reason = await denyReason(guard.path, guard.env, payload);
        // Throwing aborts the tool call in opencode's plugin system
        if (reason) throw new Error(reason);
      }
    },
  };
};
