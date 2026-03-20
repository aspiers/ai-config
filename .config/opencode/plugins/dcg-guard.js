// opencode plugin adapter for dcg (Destructive Command Guard).
//
// dcg was designed for Claude Code's PreToolUse hook protocol, which
// natively pipes JSON to a subprocess's stdin and interprets JSON
// responses. opencode's plugin system is purely in-process JS, so
// this plugin bridges the gap by doing the spawn/pipe/parse manually.
//
// Protocol: send {"tool_name", "tool_input"} on stdin.
// dcg writes nothing on stdout for allowed commands, or a JSON object
// with hookSpecificOutput.permissionDecision === "deny" for blocked ones.

export const DcgGuard = async () => {
  const dcg = Bun.which("dcg");
  if (!dcg) return {};

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const payload = JSON.stringify({
        tool_name: "Bash",
        tool_input: { command: output.args.command },
      });
      const proc = Bun.spawn([dcg], {
        stdin: "pipe",
        stdout: "pipe",
        stderr: "pipe",
        env: { ...process.env, DCG_ROBOT: "1" },
      });
      proc.stdin.write(payload);
      proc.stdin.end();
      const [, out] = await Promise.all([
        proc.exited,
        new Response(proc.stdout).text(),
      ]);
      // Empty stdout means dcg allowed the command
      const last = out.trimEnd().split("\n").pop();
      if (!last) return;
      const result = JSON.parse(last);
      if (result?.hookSpecificOutput?.permissionDecision === "deny") {
        // Throwing aborts the tool call in opencode's plugin system
        const reason =
          result.hookSpecificOutput.permissionDecisionReason ??
          "blocked by dcg";
        throw new Error(reason);
      }
    },
  };
};
