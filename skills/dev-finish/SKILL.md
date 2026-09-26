---
name: dev-finish
description: "Perform an explicitly authorized Git delivery action for verified/reviewed work: local commit, push and PR, merge, preserve, or discard. Inspect exact scope and current evidence first. Permission for one action does not imply permission for another."
---

# Dev Finish

Deliver only what the user authorized.

Read `references/dev-baseline.md`.

## Preflight

Inspect the actual repository root, branch or detached HEAD, current commit, index, working tree, remotes, upstream, and worktrees as relevant.

Preserve unrelated work and partial staging. Do not stash, reset, or discard user changes just to obtain a clean tree.

Confirm that the exact files or commit being delivered have sufficient verification and review evidence for the requested action. Reuse evidence when it still covers the same state.

If the requested finish action is already clear, do not present another menu. Ask only for a genuinely missing destination, destructive scope, or other material choice.

## Commit

For a requested commit:

- inspect the exact staged snapshot;
- stage only authorized files or hunks;
- write the message from the actual change and repository history;
- preserve unrelated index entries.

A commit request does not authorize a push.

## Push and pull request

Confirm remote, source branch, and base branch from repository state and the user's request.

Check for an existing pull request before creating a duplicate. Push only the intended commits. Do not force-push by default.

A request to create a PR normally includes the push required to publish that branch, unless the user explicitly limits it.

Use a concise PR description: problem, change, verification, and known limits.

## Merge, preserve, or discard

For merge, verify the intended target and the exact commits. Do not infer the destination only from a merge base.

For preserve, report the branch/commit/path and leave it intact.

For discard or cleanup, identify the exact data that will be lost and confirm that the user authorized that specific destructive scope. Delete only task-owned branches/worktrees after confirming they are merged or intentionally abandoned.

## Report

Return the concrete result:

- commit hash;
- PR link;
- merge target;
- preserved branch/path; or
- exact discarded scope.

Include relevant verification and any unfinished gate.

## Multi-agent use

Keep Git mutations with the main agent. Verifiers and reviewers may work in separate read-only lanes, but workers do not independently push, merge, or delete shared work.
