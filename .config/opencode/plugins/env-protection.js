const ENV_SAFE_PATTERN = /\.env(\.[^.]+)?\.example$/

const isSensitiveEnvFile = (filePath) =>
  filePath.includes(".env") && !ENV_SAFE_PATTERN.test(filePath)

export const EnvProtection = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read" && isSensitiveEnvFile(output.args.filePath)) {
        throw new Error("Do not read .env files")
      }
    },
  }
}
