export const NotificationPlugin = async ({ $, client, directory, worktree }) => {
  // console.log("NotificationPlugin loaded!");
  const fs = await import('fs');
  const { execSync, spawnSync, spawn } = await import('child_process');
  const logPath = '/tmp/opencode-notification-plugin.log';

  const logWithDate = (msg) => {
    fs.appendFileSync(logPath, new Date().toISOString() + ' ' + msg + '\n');
  };

  const hasCommand = (cmd) => {
    try {
      execSync(`which ${cmd}`, { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  };

  return {
    event: async ({ event }) => {
      logWithDate(JSON.stringify(event));
      if (event.type === "session.idle") {
          logWithDate(`Started handling ${event.type} event`);
          try {
              // Play sound notification
              if (hasCommand('mplayer')) {
                  try {
                      const mlogFd = fs.openSync('/tmp/opencode-mplayer.log', 'a');
                      spawnSync('mplayer', ['-volume', '50', '/usr/share/sounds/Oxygen-Sys-App-Positive.ogg'], {
                          timeout: 10000,
                          stdio: ['ignore', mlogFd, mlogFd],
                      });
                      fs.closeSync(mlogFd);
                  } catch (e) {
                      logWithDate(`mplayer failed: ${e}`);
                  }
              } else {
                  logWithDate('mplayer not found on PATH, skipping sound');
              }

              // Gather session context for notifications
              const sessionID = event.properties?.sessionID;
              let title = worktree || directory || 'unknown';
              let lastPrompt = '';
              if (sessionID) {
                  try {
                      const session = await client.session.get({ path: { id: sessionID } });
                      if (session?.data?.title) {
                          title = session.data.title;
                      }
                      const messages = await client.session.messages({ path: { id: sessionID } });
                      if (messages?.data) {
                          // Find the last user message
                          const userMessages = messages.data.filter(m => m.info?.role === 'user');
                          const lastUserMsg = userMessages[userMessages.length - 1];
                          if (lastUserMsg?.parts) {
                              const textPart = lastUserMsg.parts.find(p => p.type === 'text');
                              if (textPart?.text) {
                                  // Truncate to reasonable length for notification
                                  lastPrompt = textPart.text.slice(0, 100);
                                  if (textPart.text.length > 100) lastPrompt += '...';
                              }
                          }
                      }
                  } catch (e) {
                      logWithDate(`Failed to get session info: ${e}`);
                  }
              }

              // Desktop notification via notify-send
              const body = lastPrompt ? `${title}\n\n${lastPrompt}` : title;
              if (hasCommand('notify-send')) {
                  try {
                      const logFd = fs.openSync('/tmp/opencode-notify-send.log', 'a');
                      spawnSync('notify-send', ['opencode finished', body], {
                          timeout: 5000,
                          stdio: ['ignore', logFd, logFd],
                      });
                      fs.closeSync(logFd);
                  } catch (e) {
                      logWithDate(`notify-send failed: ${e}`);
                  }
              } else {
                  logWithDate('notify-send not found on PATH, skipping notification');
              }

              // ntfy.sh push notification via ACFS notify library
              // acfs_notify backgrounds curl via (curl ...) & disown, so
              // execSync kills it before completion. Use spawn+detached
              // to let the process tree outlive the event handler.
              if (hasCommand('notify-agent-idle')) {
                  try {
                      const hookInput = JSON.stringify({
                          hook_event_name: 'Stop',
                          session_id: sessionID || 'unknown',
                          agent_type: 'opencode',
                          cwd: worktree || directory || process.cwd(),
                          title: title,
                          last_prompt: lastPrompt,
                      });
                      logWithDate(`notify-agent-idle: sending hookInput (${hookInput.length} bytes)`);
                      const naiLogFd = fs.openSync('/tmp/opencode-notify-agent-idle.log', 'a');
                      const child = spawn('notify-agent-idle', [], {
                          detached: true,
                          stdio: ['pipe', naiLogFd, naiLogFd],
                      });
                      child.stdin.end(hookInput);
                      child.unref();
                      // Don't closeSync — detached process still needs the fd
                      logWithDate('notify-agent-idle: spawned detached');
                  } catch (e) {
                      logWithDate(`notify-agent-idle failed: ${e}`);
                  }
              } else {
                  logWithDate('notify-agent-idle not found on PATH, skipping ntfy notification');
              }
          } catch (err) {
              logWithDate(`ERROR: ${err}`);
          }
      }
      logWithDate(`Finished handling ${event.type} event`);
    },
  };
};
