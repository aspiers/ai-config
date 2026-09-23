// Orca plugin worker entry. Orca forks this as plain Node (no Electron) and
// hands it only PATH and HOME, so the work itself stays in the tested
// orca-cycle-attention-agent script; this file just wires commands to it.
import { execFile } from "node:child_process";
import { join } from "node:path";

const SCRIPT = "orca-cycle-attention-agent";
const SCRIPT_TIMEOUT_MS = 20_000;

function run(file, args) {
  return new Promise((resolve, reject) => {
    execFile(
      file,
      args,
      { timeout: SCRIPT_TIMEOUT_MS },
      (error, stdout, stderr) => {
        if (error) {
          error.stderr = stderr;
          reject(error);
        } else {
          resolve(stdout);
        }
      },
    );
  });
}

export async function cycle(direction, runner = run, env = process.env) {
  try {
    return await runner(SCRIPT, [direction]);
  } catch (error) {
    if (error?.code !== "ENOENT") {
      const detail = error?.stderr?.trim() || error?.message || String(error);
      throw new Error(`${SCRIPT} ${direction} failed: ${detail}`);
    }
    // Orca launched from a desktop session may carry a PATH without ~/bin,
    // where the stow deployment puts the script.
    return runner(join(env.HOME ?? "", "bin", SCRIPT), [direction]);
  }
}

export default function activate(orca) {
  orca.commands.register("next-attention-agent", () => cycle("next"));
  orca.commands.register("previous-attention-agent", () => cycle("previous"));
}
