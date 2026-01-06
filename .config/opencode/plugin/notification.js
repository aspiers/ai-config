export const NotificationPlugin = async ({ $, client, directory, worktree }) => {
  // console.log("NotificationPlugin loaded!");
  const fs = await import('fs');
  const logPath = '/tmp/opencode-notification-plugin.log';

  const logWithDate = (msg) => {
    fs.appendFileSync(logPath, new Date().toISOString() + ' ' + msg + '\n');
  };

  return {
    event: async ({ event }) => {
      logWithDate(JSON.stringify(event));
      if (event.type === "session.idle") {
          logWithDate(`Started handling ${event.type} event`);
          $.throws(true);
          try {
              const result = await $`mplayer -volume 50 /usr/share/sounds/Oxygen-Sys-App-Positive.ogg &>> /tmp/wtf.log`;
              // logWithDate('result: ' + JSON.stringify(result));
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
              const body = lastPrompt ? `${title}\n\n${lastPrompt}` : title;
              const result2 = await $`notify-send 'opencode finished' ${body} &>> /tmp/opencode-notify-send.log`;
              // logWithDate(JSON.stringify(result2));
          } catch (err) {
              logWithDate(`ERROR: ${err}`);
          }
      }
      logWithDate(`Finished handling ${event.type} event`);
    },
  };
};
