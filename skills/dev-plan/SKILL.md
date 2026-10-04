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

## Validate the decomposition

For non-trivial plans, validate the work and choices before turning them into an execution sequence. Small, obvious changes can use a compact ordered list without AND/OR labels, a graph, or extra sections.

- Distinguish required work (**AND**, all parts are needed) from genuine alternative approaches (**OR**, choose one path). Select one viable OR path for execution; do not schedule rejected alternatives as additional work. Name shared prerequisites once.
- Make dependencies directional: say what must finish before each dependent step can start. Every leaf must be an executable action or an independently verifiable outcome, with a bounded target and an observable completion condition.
- Map every acceptance criterion to one or more steps and to its verification. Check that the chosen path covers the requirements and respects the constraints and non-goals.
- Identify cycles, uncovered requirements, unchosen alternatives, and feasibility blockers. Name the affected requirement or step and the reason. Repair the decomposition and recheck it, or stop dependent work; do not mark an invalid plan `READY`.

When evidence is needed to choose an approach, plan a bounded investigation and a decision checkpoint. Keep the dependent implementation blocked until one approach is chosen; do not turn both alternatives into implementation tasks.

## Plan the work

Prefer one coherent approach that fits the existing architecture.

Compare alternatives only when there is a real choice. Do not invent options to fill a template. For a material choice, use the optional `Decisions` section to record the decision, alternatives considered, criteria and rationale, and affected requirements or steps. Omit it when no choice needs a durable record.

A useful plan names:

- ordered changes and their repository targets;
- important contracts or data flows;
- dependencies and ownership;
- material risks and failure handling;
- verification for each observable requirement;
- rollout or recovery when the change can fail operationally.

Use `--quick` for a compact plan, not to skip material dependency or feasibility checks. Use `--deliberate` when migration, compatibility, security, destructive operations, or recovery risk needs explicit failure scenarios.

## Artifact

Use existing project conventions when present. Otherwise write `.agent/plans/<slug>.md`.

```markdown
# <feature> implementation plan

> Status: DRAFT | READY | BLOCKED | STALE
> Source: <request or spec; revision or dated summary when available>
> Mode: quick | default | deliberate

## Requirements
<Scope, constraints, and acceptance criteria being implemented>

## Steps
1. <Executable change or verifiable outcome; prerequisites; covered AC-* IDs>
2. <Executable change or verifiable outcome; prerequisites; covered AC-* IDs>

## Decisions
<Omit when unnecessary: decision; alternatives; criteria and rationale; affected requirements or steps>

## Risks
<Material risks and mitigations only>

## Verification
<Checks mapped to acceptance criteria and steps>

## Open questions
<Only unresolved decisions; omit when empty>

## Objective
<For non-trivial plans: one concise sentence tracing the intended outcome to requirements and constraints>
```

`READY` means the plan is current, covers the acceptance criteria, and has no unresolved material decision, invalid dependency, or feasibility blocker. For non-trivial plans, the decomposition checks above must pass. It does not mean code exists, tests pass, or implementation is authorized.

Use `DRAFT` while the plan is incomplete and `BLOCKED` when a named decision or missing fact prevents dependent work. Use `STALE` when a source change invalidates the plan's previous readiness until its affected parts are revalidated.

## Handle drift

Before relying on an existing plan, compare its source spec or request, constraints, and material decisions with the current contract. When any of these changes, mark the plan `STALE`, identify the changed input and affected sections, and trace the impact through dependent steps and verification. Do not rely on stale parts, even if the plan was previously `READY`.

Revise affected sections and recheck coverage, dependencies, choices, and feasibility before assigning `DRAFT`, `READY`, or `BLOCKED`. If inspection shows a section is unaffected, record that conclusion rather than rewriting it. Independent, unaffected work may continue within existing authorization.

Keep decisions and drift notes in the existing plan or project convention. Do not create a separate `.clarity-protocol/` directory.

## Review

For substantial or risky plans, use a separate reviewer when the runtime can provide one. Give the reviewer the source contract, draft plan, and relevant repository context.

A self-check is useful but is not independent approval. Do not manufacture planner/architect/critic consensus inside one context.

## Handoff

Return the chosen approach, plan path or inline plan, material open questions, and any evidence limits. For a non-trivial plan, finish with one concise objective sentence that traces to its requirements and constraints. Respect plan-only requests.
