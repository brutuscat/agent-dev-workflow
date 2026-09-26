---
name: dev-auto
description: "Read-only navigator for Agent Dev Workflow. Use when the user explicitly asks what step to take next or names dev-auto. Recommend the shortest useful next step from current evidence. Do not edit code, write artifacts, invoke other skills, or pretend to orchestrate a hidden workflow."
---

# Dev Auto

Recommend one useful next step. Do not execute it.

Read `references/dev-baseline.md`.

## Decide from the current state

Use the request, conversation, relevant `.agent/` artifacts, and repository state. Read only enough evidence to justify the recommendation.

A file existing does not prove that its contents are current or ready.

| Need | Next step |
|---|---|
| Behavior, scope, or acceptance is unclear | `dev-spec` |
| Scope is clear but implementation has meaningful sequencing, trade-offs, migration, compatibility, security, or recovery risk | `dev-plan` |
| Scoped behavior is ready to implement | `dev-tdd` |
| Something is broken and the cause is not proven | `dev-fix` |
| Implementation exists and someone is about to claim completion | `dev-verify` |
| The diff needs a defect pass before delivery | `dev-code-review` |
| Verified/reviewed work needs an authorized Git action | `dev-finish` |

These are not mandatory phases. A small clear change may skip `dev-spec` and `dev-plan`. A bug starts at `dev-fix`; do not route it through a second TDD phase afterward.

## Status

When the user asks for status, report:

- what evidence exists;
- what remains uncertain;
- what blocks the next dependent action.

Do not infer implementation, verification, review, or authorization from an artifact name or timestamp.

## Recovery

When work is stuck, name the concrete missing evidence or decision and the smallest action that can resolve it.

Do not recommend repeating the same failed command or approach unless something relevant changed.

## Boundaries

- Read-only.
- No artifact writes.
- No code changes.
- No Git mutations.
- No subagent delegation.
- No automatic skill invocation.

If several unrelated work items are plausible and the choice changes the answer, ask which one. Otherwise make the best grounded recommendation without a confirmation round.
