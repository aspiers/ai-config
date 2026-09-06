---
description: Rebase every local branch onto the moved upstream and rebuild the mixdown
argument-hint: "[upstream-ref-or-scope]"
allowed-tools: Skill(git-rebase-all)
---

Use the `git-rebase-all` skill to survey the local branches against the
upstream, rebase each onto its new base in dependency order, flag any that
upstream has superseded, and rebuild the mixdown branch that combines them.

Additional context: $ARGUMENTS
