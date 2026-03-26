---
name: linear-ready
description: Find Linear issues ready for an AI agent to pick up. Equivalent of `bd ready` for Linear workflows. Use when starting a session to find claimable work, or when asked "what's next" or "find work".
---

# Linear Ready

Find Linear issues that are ready for an AI agent to work on — meaning
they match your filters and have no active (unresolved) blockers.

This is the Linear equivalent of `bd ready` in beads workflows.

## Prerequisites

1. **linear-cli** must be installed and authenticated:

   ```bash
   brew install schpet/tap/linear   # or: npm install -g @schpet/linear-cli
   linear auth login
   ```

2. **jq** must be available on PATH.

## How It Works

The script runs a **single GraphQL query** via `linear api` that fetches
candidate issues along with their blocking relations and blocker states.
It then filters client-side with `jq`:

- An issue is **ready** if it has no `blockedBy` relations pointing to
  incomplete issues (i.e. all blockers are in a `completed`, `canceled`,
  or `duplicate` state).
- An issue is **blocked** if any of its blockers are still active.

## Label Convention

Issues suitable for AI agent work should be tagged with the **"AI"** label
in Linear. This is the default filter; override with `--label`.

## Usage

Run the script from this skill's directory:

```bash
.agents/skills/linear-ready/scripts/linear-ready [OPTIONS]
```

### Options

| Flag                | Description                                      | Default            |
| ------------------- | ------------------------------------------------ | ------------------ |
| `--team <key>`      | Filter by team key (e.g. "ENG")                  | all teams          |
| `--label <name>`    | Label to filter for                              | `AI`               |
| `--project <name>`  | Filter by project name                           |                    |
| `--assignee <name>` | Filter by assignee display name                  |                    |
| `--unassigned`      | Show only unassigned issues                      |                    |
| `--priority <1-4>`  | Filter by priority (1=Urgent..4=Low)             |                    |
| `--limit <n>`       | Max results                                      | `50`               |
| `--state <types>`   | Comma-separated state types to include           | `backlog,unstarted` |
| `--include-blocked` | Include blocked issues in output                 |                    |
| `--json`            | JSON output for agent consumption                |                    |

### Examples

```bash
# Find all ready AI issues
linear-ready

# Find ready issues for a specific team
linear-ready --team ENG

# Find ready issues in a specific project
linear-ready --team ENG --project "Auth Rewrite"

# Find unassigned ready issues (good for picking up new work)
linear-ready --unassigned

# JSON output for programmatic use
linear-ready --json

# Include blocked issues to see the full picture
linear-ready --include-blocked

# Use a different label instead of "AI"
linear-ready --label "agent-ready"
```

## Agent Workflow

When starting a session or looking for work:

1. **Find ready work:**

   ```bash
   linear-ready --team ENG --json
   ```

2. **Pick an issue** — choose the highest priority unblocked issue from
   the output.

3. **Read the issue description** for full context:

   ```bash
   linear issue view ENG-42 --json
   ```

4. **Start work** — update the issue state to "In Progress":

   ```bash
   linear issue update ENG-42 -s started
   ```

   Or use `linear issue start ENG-42` which also creates a git branch.

5. **Implement** the task following the issue's acceptance criteria.

6. **Complete** — update the issue state when done:

   ```bash
   linear issue update ENG-42 -s completed
   ```

## Output Formats

### Pretty (default)

```
Ready issues (label: AI):

  ENG-42  [High]    Add display_name to user profile
          State: Todo | Project: User Features | Unassigned

  ENG-45  [Normal]  Fix auth token refresh race condition
          State: Todo | Assigned: alice

Blocked: 2 issue(s) hidden (use --include-blocked to show)
```

### JSON (`--json`)

```json
{
  "ready": [
    {
      "identifier": "ENG-42",
      "title": "Add display_name to user profile",
      "priority": 2,
      "priorityLabel": "High",
      "url": "https://linear.app/...",
      "state": { "name": "Todo", "type": "unstarted" },
      "assignee": null,
      "project": { "name": "User Features" },
      "activeBlockers": []
    }
  ],
  "blockedCount": 2
}
```

With `--include-blocked --json`, the full `blocked` array is included
with each issue's `activeBlockers` list showing what's blocking it.
