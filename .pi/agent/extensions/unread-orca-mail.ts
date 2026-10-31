/**
 * Orca unread-mail extension for pi.
 *
 * Pi's counterpart of the ai-guard-orca-unread-mail Claude Code Stop hook.
 * When the agent ends its turn inside an Orca terminal with orchestration
 * mail it has not read, start another turn listing that mail. The guard
 * raises each message once, so this cannot loop.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const GUARD = "ai-guard-orca-unread-mail";

export default function orcaUnreadMailExtension(pi: ExtensionAPI) {
	pi.on("agent_end", async () => {
		if (!process.env.ORCA_TERMINAL_HANDLE) return;
		// A missing guard or failed check must not get in the agent's way.
		const result = await pi.exec(GUARD, ["--text"]).catch(() => undefined);
		const reason = result?.code === 0 ? result.stdout.trim() : "";
		if (!reason) return;
		pi.sendMessage(
			{ customType: "orca-unread-mail", content: reason, display: true },
			{ triggerTurn: true, deliverAs: "followUp" },
		);
	});
}
