---
name: dev-plan
description: "Create a repository-grounded implementation plan for a clear request or spec. Use when sequencing, dependencies, trade-offs, migration, compatibility, security, recovery, or coordination risk makes planning useful. Planning does not authorize implementation."
---

# Dev Plan

Create the smallest plan that makes implementation safer and more predictable.

Read `references/dev-baseline.md`.

## Establish the contract

Use the request and any relevant `.agent/specs/<slug>.md` as the source of truth. Read the implementation, callers, tests, configuration, and existing project decisions before naming files or symbols.

If a missing product decision changes the solution, stop the dependent part and ask for that decision. Continue planning independent parts.

Do not require a spec file when the request is already clear.

## Plan the work

Prefer one coherent approach that fits the existing architecture.

Compare alternatives only when there is a real choice. Do not invent options to fill a template.

A useful plan names:

- ordered changes and their repository targets;
- important contracts or data flows;
- dependencies and ownership;
- material risks and failure handling;
- verification for each observable requirement;
- rollout or recovery when the change can fail operationally.

Use `--quick` for a compact plan. Use `--deliberate` when migration, compatibility, security, destructive operations, or recovery risk needs explicit failure scenarios.

## Artifact

Use existing project conventions when present. Otherwise write `.agent/plans/<slug>.md`.

```markdown
# <feature> implementation plan

> Status: DRAFT | READY | BLOCKED
> Source: <request or spec>
> Mode: quick | default | deliberate

## Requirements
<Scope and acceptance criteria being implemented>

## Steps
1. <Concrete repository change>
2. <Concrete repository change>

## Risks
<Material risks and mitigations only>

## Verification
<Checks mapped to requirements>

## Open questions
<Only unresolved decisions; omit when empty>
```

`READY` means the plan itself has no unresolved technical decision that blocks implementation. It does not mean code exists, tests pass, or implementation is authorized.

## Review

For substantial or risky plans, use a separate reviewer when the runtime can provide one. Give the reviewer the source contract, draft plan, and relevant repository context.

A self-check is useful but is not independent approval. Do not manufacture planner/architect/critic consensus inside one context.

## Handoff

Return the chosen approach, plan path or inline plan, material open questions, and any evidence limits. Respect plan-only requests.
