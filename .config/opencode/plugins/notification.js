export const NotificationPlugin = async ({ $, client, directory, worktree }) => {
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

    // Run a command synchronously, logging output to a dedicated file
    const runLogged = (logFile, cmd, args, opts = {}) => {
        const fd = fs.openSync(logFile, 'a');
        try {
            spawnSync(cmd, args, { stdio: ['ignore', fd, fd], ...opts });
        } finally {
            fs.closeSync(fd);
        }
    };

    const ringBell = () => {
        // Write BEL to the controlling terminal, bypassing any stdout
        // redirection, so tmux sets window_bell_flag.
        const ttyFd = fs.openSync('/dev/tty', 'w');
        try {
            fs.writeSync(ttyFd, '\x07');
        } finally {
            fs.closeSync(ttyFd);
        }
    };

    const playSound = () => {
        runLogged('/tmp/opencode-mplayer.log',
            'mplayer', ['-volume', '50', '/usr/share/sounds/Oxygen-Sys-App-Positive.ogg'],
            { timeout: 10000 });
    };

    const getSessionContext = async (sessionID) => {
        let title = worktree || directory || 'unknown';
        let lastPrompt = '';
        if (!sessionID) return { title, lastPrompt };

        const session = await client.session.get({ path: { id: sessionID } });
        if (session?.data?.title) {
            title = session.data.title;
        }

        const messages = await client.session.messages({ path: { id: sessionID } });
        if (messages?.data) {
            const userMessages = messages.data.filter(m => m.info?.role === 'user');
            const lastUserMsg = userMessages[userMessages.length - 1];
            const textPart = lastUserMsg?.parts?.find(p => p.type === 'text');
            if (textPart?.text) {
                lastPrompt = textPart.text.slice(0, 100);
                if (textPart.text.length > 100) lastPrompt += '...';
            }
        }

        return { title, lastPrompt };
    };

    const sendDesktopNotification = (title, lastPrompt) => {
        const body = lastPrompt ? `${title}\n\n${lastPrompt}` : title;
        runLogged('/tmp/opencode-notify-send.log',
            'notify-send', ['opencode finished', body],
            { timeout: 5000 });
    };

    // Spawn detached so the process tree outlives the event handler;
    // acfs_notify backgrounds curl via (curl ...) & disown, which
    // execSync would kill before completion.
    const sendPushNotification = (sessionID, title, lastPrompt) => {
        const hookInput = JSON.stringify({
            hook_event_name: 'Stop',
            session_id: sessionID || 'unknown',
            agent_type: 'opencode',
            cwd: worktree || directory || process.cwd(),
            title,
            last_prompt: lastPrompt,
        });
        logWithDate(`notify-agent-idle: sending hookInput (${hookInput.length} bytes)`);
        const fd = fs.openSync('/tmp/opencode-notify-agent-idle.log', 'a');
        const child = spawn('notify-agent-idle', [], {
            detached: true,
            stdio: ['pipe', fd, fd],
        });
        child.stdin.end(hookInput);
        child.unref();
        // Don't closeSync — detached process still needs the fd
        logWithDate('notify-agent-idle: spawned detached');
    };

    // Run a notification step, logging failures without propagating
    const attempt = (label, fn) => {
        try {
            return fn();
        } catch (e) {
            logWithDate(`${label} failed: ${e}`);
        }
    };

    const attemptAsync = async (label, fn) => {
        try {
            return await fn();
        } catch (e) {
            logWithDate(`${label} failed: ${e}`);
        }
    };

    const handleSessionIdle = async (event) => {
        logWithDate(`Started handling ${event.type} event`);

        attempt('bell', ringBell);

        if (hasCommand('mplayer')) {
            attempt('mplayer', playSound);
        } else {
            logWithDate('mplayer not found on PATH, skipping sound');
        }

        const sessionID = event.properties?.sessionID;
        const { title, lastPrompt } = await attemptAsync(
            'session context', () => getSessionContext(sessionID)
        ) || { title: worktree || directory || 'unknown', lastPrompt: '' };

        if (hasCommand('notify-send')) {
            attempt('notify-send', () => sendDesktopNotification(title, lastPrompt));
        } else {
            logWithDate('notify-send not found on PATH, skipping notification');
        }

        if (hasCommand('notify-agent-idle')) {
            attempt('notify-agent-idle', () => sendPushNotification(sessionID, title, lastPrompt));
        } else {
            logWithDate('notify-agent-idle not found on PATH, skipping ntfy notification');
        }
    };

    return {
        event: async ({ event }) => {
            logWithDate(JSON.stringify(event));
            if (event.type === "session.idle") {
                try {
                    await handleSessionIdle(event);
                } catch (err) {
                    logWithDate(`ERROR: ${err}`);
                }
            }
            logWithDate(`Finished handling ${event.type} event`);
        },
    };
};
