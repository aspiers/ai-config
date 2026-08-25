# Generic skills context-engineering audit

## Source and scope

This audit applies the principles in
[Thariq Shams's context-engineering post][source] to reusable skills under
`.agents/skills/`.

The audit includes cross-site browser automation, agent authoring, Beads, Git,
code quality, planning, task workflows, Pi package management, and generic file
conversion. It excludes application-specific `hubdoc-reviewer`,
`obs-management`, `xero-browser`, and `xero-mcp`; their domain knowledge needs a
separate audit rather than generic simplification.

The source recommends:

- letting capable models use judgement instead of accumulating guardrails;
- designing expressive tool and script interfaces instead of prescribing an
  exploration path through examples;
- loading detail progressively rather than putting everything up front;
- keeping tool descriptions simple and avoiding repeated instructions; and
- using skills for particular opinions, knowledge, and gotchas rather than
  obvious general advice.

Strictness is still appropriate where an error is destructive, publishes data,
breaks an external protocol, or violates explicit repository policy.

## Findings

The recurring issues were:

1. **Absolute rules without an invariant.** Several skills use “always,”
   “never,” fixed line limits, mandatory pauses, or fixed command sequences for
   decisions better informed by the user request and repository context.
2. **Repeated ownership.** Linting, testing, staging, committing, and user
   approval are described independently in multiple task-workflow skills.
3. **Examples as specifications.** Long examples in Git, authoring, planning,
   and Linear skills encourage copying one workflow instead of exposing the
   real decision interface.
4. **Conditional detail loaded eagerly.** API queries, patch syntax, platform
   frontmatter, and troubleshooting catalogs often live directly in
   `SKILL.md` despite being needed only on one branch of the workflow.
5. **Generic knowledge with little local value.** Some skills explain DRY,
   small functions, testing, or documentation at textbook level rather than
   recording project-specific judgement and gotchas.
6. **Descriptions that under-route.** A few descriptions say what a skill does
   but omit important trigger language; others expose a narrow historical use
   while the body claims a broader workflow.

## Per-skill audit

Priority means urgency for a follow-up change, not the importance of the
skill. “Keep” means no material context-engineering problem was found.

| Skill                     | Assessment and proposal                                                                                                                                                                                                       | Priority |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `agent-browser-local`     | Valuable empirical gotchas. Keep the interaction loop in `SKILL.md`; move widget recipes and dated provenance into direct references.                                                                                         | P1       |
| `agent-browser-viewport`  | Keep. It documents a focused script interface and the non-obvious pixel calculation behind it. The script owns the fragile operation.                                                                                         | Keep     |
| `agent-command-authoring` | Split platform syntax, examples, and verification into `references/claude-code.md`, `references/opencode.md`, and `references/pi.md`. Keep only the delegation decision and routing table up front.                           | P0       |
| `allow-agent-commands`    | Generalize discovery around repository policy. Remove automatic stage/commit behavior and hard-coded repository paths, or mark the skill explicitly author-specific if those paths are intentional.                           | P1       |
| `beads`                   | Keep the durable-task boundary and link to `beads-best-practices`; trim CLI examples already discoverable through `bd prime` and `bd --help`.                                                                                 | P2       |
| `beads-best-practices`    | The policy is useful but long. Keep claim/tracking invariants up front and split Markdown examples and comment-writing detail into references.                                                                                | P1       |
| `beads-solo`              | Keep. Its strictness enforces an explicit opt-in and protects Git/Dolt publication boundaries; one-off repair detail is already disclosed through a reference.                                                                | Keep     |
| `checking-upstream`       | Keep. It is concise, judgement-oriented, and contributes a non-obvious research checkpoint without prescribing one tracker implementation.                                                                                    | Keep     |
| `code-linting`            | **Implemented:** defer to repository commands, authorize mutating fixes contextually, and distinguish introduced, pre-existing, and environment findings.                                                                     | Done     |
| `code-refactoring-dry`    | **Implemented:** replace the universal DRY rule with a decision about shared concepts, coupling, and maintenance value.                                                                                                       | Done     |
| `code-refactoring-small`  | **Implemented:** remove arbitrary line thresholds and optimize for cohesion and comprehensibility instead.                                                                                                                    | Done     |
| `code-reviewing`          | **Implemented:** replace mechanical limits with risk-based review priorities and require plausible, located findings.                                                                                                         | Done     |
| `describing-prs`          | Let repository PR templates and history determine sections. Keep the merge-base helper interface; move its strategy and output example behind `--help` or a reference.                                                        | P1       |
| `documentation-updates`   | **Implemented:** route durable knowledge to its authoritative home, avoid obvious/transient/private content, and remove the unconditional approval stop.                                                                      | Done     |
| `editorconfig`            | Remove the fixed generated template and universal Markdown/JSON choices. Preserve only evidence gathering, minimal generation, and validation against repository style.                                                       | P1       |
| `git-commit`              | **Implemented:** preserve the index boundary, match repository history before assuming Conventional Commits, and add metadata only when required.                                                                             | Done     |
| `git-staging`             | **Implemented:** reduce the main workflow to boundary selection and verification; move line-level patch mechanics into `references/partial-staging.md`.                                                                       | Done     |
| `incremental-commits`     | **Implemented:** replace the fixed five-wave schema example with dependency-aware judgement and meaningful intermediate-state criteria.                                                                                       | Done     |
| `iterative-development`   | Preserve approval checkpoints only when the user requests collaborative iteration. Remove all-caps repetition and assumptions about `.ai/` files or one-item internal TODO lists.                                             | P0       |
| `linear-ready`            | Keep the script as the interface. Replace duplicated options, examples, and output schemas with a short invocation, `--help`, readiness semantics, and the claim handoff.                                                     | P1       |
| `managing-pi-packages`    | Preserve strict audit constraints because extensions execute with user privileges. Progressive references already work; move author-specific development-fork conventions and longer lifecycle detail out of the common path. | P2       |
| `plan-to-beads`           | Split issue-quality criteria, body template, and CLI recipes into references. Replace “100% self-contained/zero questions” with enough context for the task and explicit uncertainty where discovery cannot remove it.        | P0       |
| `plan-to-linear`          | Apply the same issue-quality reference split; move MCP setup and field syntax to platform references and let workspace conventions choose grouping.                                                                           | P0       |
| `pr-comment-resolving`    | Keep the four-surface completeness invariant, but move GraphQL/REST recipes, pagination, reply mutations, and bot tables into references selected after PR discovery.                                                         | P0       |
| `project-initialization`  | **Implemented:** inspect harness discovery before choosing links, avoid mandatory renames, keep entry instructions lightweight, and scope command-safety review to real risk.                                                 | Done     |
| `prp-generation`          | Remove the exact conversational sequence, junior-developer assumption, fixed `.ai/` path, and mandatory question count. Ask only for material missing context and follow repository planning conventions.                     | P1       |
| `safe-rm`                 | Preserve low freedom because deletion is destructive and the tested script is the interface. Trim implementation internals and examples from `SKILL.md`; expose behavior and recovery through `--help` or a reference.        | P2       |
| `skill-authoring`         | **Implemented:** make judgement, interface design, progressive disclosure, single ownership, and justified strictness the review rubric.                                                                                      | Done     |
| `slow-command-running`    | **Implemented:** use output capture selectively, distinguish one-shot logs from managed background processes, preserve producer exit status, and avoid sensitive logs.                                                        | Done     |
| `subagent-authoring`      | Split Claude Code and OpenCode schemas, permissions, and examples into platform references. Keep only thin-wrapper ownership and the mode decision in `SKILL.md`.                                                             | P0       |
| `task-generation`         | Remove mandatory “go” pauses, committing, fixed `.ai/` paths, and junior framing. Generate detail proportionate to uncertainty and use the repository's task system.                                                          | P1       |
| `task-implementation`     | Replace duplicated lint/test discovery with links to owning skills. Remove exact sequencing and role-play; define inputs, authority boundaries, implementation outcome, and handoff evidence.                                 | P0       |
| `task-orchestration`      | Remove the fixed “good/vibe” protocol and repeated child workflows. Keep orchestration state, user checkpoints requested by the active workflow, and delegation to owning skills.                                             | P0       |
| `test-running`            | **Implemented:** select tests by behavior and risk, distinguish regressions from infrastructure/pre-existing failures, and report the actual coverage boundary.                                                               | Done     |
| `xlsx-to-csv`             | Keep. It is concise operational knowledge: the active-sheet trap, multi-sheet interface, and mislabeled XLSX detection are not obvious generic advice.                                                                        | Keep     |

## Implemented changes

This pass updates the shared authoring standard and the generic skills with the
widest day-to-day effect:

- rewrote `skill-authoring` around judgement, interface design, progressive
  disclosure, single ownership, and narrow justified strictness;
- simplified Git commit boundaries and dependency-aware commit planning;
- split partial Git staging mechanics into an on-demand reference;
- made linting, testing, review, and refactoring responsive to repository
  context rather than arbitrary absolutes;
- routed documentation lessons to authoritative durable locations;
- distinguished expensive one-shot output capture from managed background
  processes; and
- made project initialization discover and preserve repository conventions
  rather than enforcing one file layout.

The remaining proposals are tracked in three follow-up beads:

- `ai-u4f` — split generic authoring and PR-review skills by platform and API
  surface;
- `ai-jr6` — simplify generic planning and task workflow skills; and
- `ai-76s` — tighten the remaining generic utility skills.

Applying all proposals in one edit would make review difficult and risks
changing mature operational workflows without dedicated tests; the audit
therefore groups that work into reviewable follow-ups rather than silently
expanding this pass.

## Review standard for follow-up work

A follow-up is complete when it can answer:

1. What non-obvious knowledge does the skill add?
2. Which constraints protect a real invariant, and why?
3. Which decisions should remain contextual?
4. What detail can move behind a reference or tested script?
5. Which instruction is duplicated from another skill or tool description?
6. Does frontmatter route the skill without loading its workflow globally?
7. Can the resulting behavior be validated without relying on examples as the
   specification?

[source]: https://x.com/trq212/status/2080710971228918066
