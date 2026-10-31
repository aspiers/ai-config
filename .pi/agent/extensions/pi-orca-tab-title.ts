// Pin a Pi session's short title as its Orca tab's custom title, so the tab bar
// and Activity sidebar show it, and Orca's synthetic "Pi ready" title can't
// replace it. The short title comes from pi-tmux-window-name's custom entry;
// an explicit /name, or a session without one, uses the session name.

import type { ExtensionAPI, SessionEntry } from "@earendil-works/pi-coding-agent";

const WINDOW_NAME_ENTRY_TYPE = "pi-tmux-window-name/window";
// Each attempt spawns the Orca CLI, so a stale terminal handle mustn't retry forever.
const MAX_RENAME_FAILURES = 3;

export function resolveOrcaTitle(entries: SessionEntry[], sessionName: string): string {
  let sessionInfoIndex = -1;

  for (let i = entries.length - 1; i >= 0; i -= 1) {
    const entry = entries[i];
    if (sessionInfoIndex < 0 && entry.type === "session_info") {
      sessionInfoIndex = i;
    }
    if (entry.type !== "custom" || entry.customType !== WINDOW_NAME_ENTRY_TYPE) continue;

    const shortName = (entry.data as { shortName?: unknown } | undefined)?.shortName;
    if (typeof shortName !== "string" || !shortName.trim()) continue;

    // pi-tmux-window-name appends its entry right after setting the session
    // name, so a newer session_info means a manual /name, which wins.
    return i > sessionInfoIndex ? shortName : sessionName;
  }

  return sessionName;
}

// Herdr and tmux panes inherit Orca's environment but own their own tab labels.
export function orcaTerminalHandle(environment: NodeJS.ProcessEnv): string | undefined {
  if (environment.HERDR_ENV === "1" || environment.TMUX) return undefined;
  return environment.ORCA_TERMINAL_HANDLE || undefined;
}

export default function (pi: ExtensionAPI) {
  const handle = orcaTerminalHandle(process.env);
  if (!handle) return;
  const orcaCli = process.env.ORCA_CLI_COMMAND || "orca-ide";

  let lastSynced: string | undefined;
  let failures = 0;

  async function sync(ctx: { hasUI: boolean; sessionManager: { getBranch(): SessionEntry[] } }) {
    // Print mode has no tab of its own: it is usually a tool run inside another agent.
    if (!ctx.hasUI || failures >= MAX_RENAME_FAILURES) return;
    const sessionName = pi.getSessionName();
    if (!sessionName) return;

    const title = resolveOrcaTitle(ctx.sessionManager.getBranch(), sessionName);
    if (title === lastSynced) return;
    lastSynced = title;

    const result = await pi
      .exec(orcaCli, ["terminal", "rename", "--terminal", handle, "--title", title])
      .catch(() => ({ code: 1 }));
    if (result.code === 0) {
      failures = 0;
    } else {
      failures += 1;
      lastSynced = undefined;
    }
  }

  pi.on("session_start", (_event, ctx) => {
    lastSynced = undefined;
    void sync(ctx);
  });
  pi.on("session_info_changed", (_event, ctx) => {
    // pi-tmux-window-name appends its entry just after setSessionName().
    queueMicrotask(() => void sync(ctx));
  });
  pi.on("agent_start", (_event, ctx) => void sync(ctx));
}
