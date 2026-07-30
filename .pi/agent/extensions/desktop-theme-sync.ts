import { readFileSync, watch, type FSWatcher } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

type Appearance = "light" | "dark";
type ThemeMapping = Record<Appearance, string>;

const desktopThemeDirectory =
  process.env.XDG_CONFIG_HOME ?? join(homedir(), ".config");
const desktopThemeFilename = "theme";
const desktopThemePath = join(desktopThemeDirectory, desktopThemeFilename);
const themeSyncConfigPath = join(homedir(), ".pi", "agent", "theme-sync.json");
const defaultThemes: ThemeMapping = {
  light: "catppuccin-latte",
  dark: "catppuccin-mocha",
};

function readDesktopAppearance(): Appearance | undefined {
  try {
    const appearance = readFileSync(desktopThemePath, "utf8").trim();
    return appearance === "light" || appearance === "dark" ? appearance : undefined;
  } catch {
    return undefined;
  }
}

function readThemeMapping(): ThemeMapping {
  try {
    const config = JSON.parse(readFileSync(themeSyncConfigPath, "utf8")) as {
      themes?: Partial<ThemeMapping>;
    };
    return {
      light: config.themes?.light ?? defaultThemes.light,
      dark: config.themes?.dark ?? defaultThemes.dark,
    };
  } catch {
    return defaultThemes;
  }
}

function applyDesktopTheme(
  ctx: ExtensionContext,
  themes: ThemeMapping,
): Appearance | undefined {
  const appearance = readDesktopAppearance();
  if (!appearance) return undefined;

  const desiredTheme = themes[appearance];
  if (ctx.ui.theme.name !== desiredTheme) {
    ctx.ui.setTheme(desiredTheme);
  }
  return appearance;
}

export default function desktopThemeSync(pi: ExtensionAPI) {
  let generation = 0;
  let watcher: FSWatcher | undefined;

  const cleanup = () => {
    generation += 1;
    watcher?.close();
    watcher = undefined;
  };

  pi.on("session_start", (_event, ctx) => {
    cleanup();
    if (ctx.mode !== "tui") return;

    const currentGeneration = generation;
    const themes = readThemeMapping();
    applyDesktopTheme(ctx, themes);

    watcher = watch(desktopThemeDirectory, (_eventType, filename) => {
      if (generation !== currentGeneration) return;
      if (filename && filename.toString() !== desktopThemeFilename) return;
      applyDesktopTheme(ctx, themes);
    });
    watcher.unref();
  });

  pi.on("session_shutdown", cleanup);

  pi.registerCommand("theme-sync", {
    description: "Show the desktop-to-Pi theme synchronization status",
    handler: (_args, ctx) => {
      const appearance = readDesktopAppearance();
      const themes = readThemeMapping();
      const desired = appearance ? themes[appearance] : "unknown";
      ctx.ui.notify(
        `Desktop: ${appearance ?? "unknown"}; Pi: ${ctx.ui.theme.name}; desired: ${desired}`,
        appearance && ctx.ui.theme.name === desired ? "info" : "warning",
      );
    },
  });
}
