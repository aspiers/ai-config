export const NotificationPlugin = async ({ $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        await $`mplayer -volume 50 /usr/share/sounds/Oxygen-Sys-App-Positive.ogg`;
        await $`notify-send 'opencode finished'`;
      }
    },
  };
};
