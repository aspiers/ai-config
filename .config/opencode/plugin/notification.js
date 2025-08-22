export const NotificationPlugin = async ({ $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        $`mplayer -volume 50 /usr/share/sounds/Oxygen-Sys-App-Positive.ogg`;
        $`notify-send 'opencode finished'`;
      }
    },
  };
};
