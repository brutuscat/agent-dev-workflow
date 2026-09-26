---
name: dev-tdd
description: "Implement a known scoped behavior with focused tests before production code when practical. Use for features, small behavior changes, and behavior-preserving refactors. Use dev-fix when the cause of broken behavior still needs investigation. Do not invent tests for documentation or formatting-only edits."
---

# Dev TDD

Use tests to prove the behavior, then make the smallest coherent change.

Read `references/dev-baseline.md`.

## Establish the behavior

Read the affected code, nearby tests, project test commands, and the relevant request/spec/plan.

State the observable behavior briefly. Ask only if a missing decision materially changes implementation and cannot be resolved from existing project evidence.

Inspect Git state before edits when it matters. Preserve unrelated staged, unstaged, and untracked work.

## Choose the proof

For new behavior or a known regression, prefer a focused test that fails on the unchanged implementation for the expected reason.

For a behavior-preserving refactor, existing or new characterization tests may already pass before the change. Keep them passing through the refactor.

Do not add a test when it would only restate a typo, formatting change, asset replacement, or another low-risk edit. Use the smallest meaningful check instead.

## Implement

1. Run the focused proof.
2. Confirm the failure is caused by the missing behavior, not a broken fixture or environment.
3. Implement the smallest coherent change.
4. Run the same proof again.
5. Expand checks only as required by blast radius or project gates.
6. Refactor only what the task needs, then rerun affected checks.

Do not weaken a correct test to make the implementation pass.

If strict red/green cannot be demonstrated because the code was already changed, say so. Post-implementation tests are useful evidence, but they are not a historical red/green cycle.

## Handoff

Report:

- behavior implemented;
- changed files;
- commands and observed results;
- important limitations or unverified boundaries.

Map evidence to `AC-*` identifiers when they exist.

No commit, push, merge, or destructive cleanup is implied by implementation.

## Multi-agent use

Delegate only a bounded implementation with explicit file ownership. Parallel workers must have disjoint write scopes.

A worker returns changed files and raw verification results. A later verifier or reviewer evaluates the final integrated state rather than trusting the worker's summary.
