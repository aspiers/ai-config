---
name: slow-command-running
description: Preserve output from expensive one-shot commands for monitoring and later analysis. Use when rerunning a build, API query, CI inspection, or diagnostic would be costly and a managed background process is not the better interface.
---

# Preserve Expensive Command Output

Capture output when it will be useful during or after a slow command. For
servers, watchers, and ongoing log streams, prefer the harness's managed
background-process tool instead of a shell pipeline.

## Pattern

Choose a repository-approved ignored path, then preserve both displayed and
saved output:

```bash
mkdir -p tmp
command 2>&1 | tee tmp/descriptive-command.log
```

Use `set -o pipefail` or inspect the producer's pipeline status when command
success matters; `tee` succeeding does not prove the original command
succeeded.

Name logs by purpose and stable identifier so concurrent runs do not overwrite
one another. Avoid recording credentials or sensitive response data.

Do not add `tee` mechanically to fast commands or output that will be consumed
only once. Avoid truncating a live producer with `head` unless early SIGPIPE
termination is intended.
