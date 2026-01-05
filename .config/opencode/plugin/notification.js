export const NotificationPlugin = async ({ $ }) => {
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
              const result2 = await $`notify-send 'opencode finished' &>> /tmp/opencode-notify-send.log`;
              // logWithDate(JSON.stringify(result2));
          } catch (err) {
              logWithDate(`ERROR: ${err}`);
          }
      }
      logWithDate(`Finished handling ${event.type} event`);
    },
  };
};
