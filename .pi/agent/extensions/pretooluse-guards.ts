/**
 * Command guards extension for pi.
 *
 * Runs command guards written as Claude Code PreToolUse hooks against every
 * bash tool call, and blocks the call when a guard denies it. The guard reads
 * {"tool_name", "tool_input"} as JSON on stdin and writes nothing for an
 * allowed command, or a JSON object with
 * hookSpecificOutput.permissionDecision === "deny" for a blocked one.
 */

import { spawnSync } from "node:child_process";

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const GUARDS = ["ai-guard-git-worktree-add"];
const GUARD_TIMEOUT_MS = 10_000;

function denyReason(guard: string, payload: string): string | undefined {
	const result = spawnSync(guard, [], {
		input: payload,
		encoding: "utf8",
		timeout: GUARD_TIMEOUT_MS,
	});
	// A missing guard must not take every bash call down with it.
	if (result.error || result.status !== 0) return undefined;

	const last = result.stdout.trimEnd().split("\n").pop();
	if (!last) return undefined;
	const output = JSON.parse(last)?.hookSpecificOutput;
	if (output?.permissionDecision !== "deny") return undefined;
	return output.permissionDecisionReason ?? `blocked by ${guard}`;
}

export default function preToolUseGuardsExtension(pi: ExtensionAPI) {
	pi.on("tool_call", async (event) => {
		if (event.toolName !== "bash") return;

		const command = (event.input as { command?: unknown }).command;
		if (typeof command !== "string" || command.length === 0) return;

		const payload = JSON.stringify({ tool_name: "Bash", tool_input: { command } });
		for (const guard of GUARDS) {
			const reason = denyReason(guard, payload);
			if (reason) return { block: true, reason };
		}
	});
}
