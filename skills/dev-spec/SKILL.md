---
name: dev-spec
description: "Turn a feature or behavior request into a small implementation-independent contract. Use when scope, observable behavior, acceptance criteria, or material assumptions need to be explicit before planning or coding. Read relevant code and docs before asking questions. Do not implement code."
---

# Dev Spec

Make the behavior clear enough that implementation and review can use the same contract.

Read `references/dev-baseline.md`.

## First inspect the repository

Read the request, relevant code, nearby tests, existing docs, and any current `.agent/specs/` artifact before asking questions.

Ask only about missing information that changes user-visible behavior, a public contract, authorization, destructive scope, or another material decision. Preserve decisions the user already made.

A clear request does not need an interview. If the intended outcome is still vague after inspection, clarify what must change and why before producing the contract. Do not invent a success target to make the request seem ready.

## Produce the contract

Use an existing project convention when one exists. Otherwise write `.agent/specs/<slug>.md`. Use chat-only output when requested.

Separate the goal from a proposed method. Preserve an explicitly required method as a constraint, not as a substitute for the outcome. Make constraints, non-goals, assumptions, and material open questions explicit in the sections below without duplicating them in `Goal`.

Keep the artifact small:

```markdown
# <feature>

> Status: DRAFT | READY | BLOCKED
> Last updated: <YYYY-MM-DD>

## Goal
<Observable outcome and desired effect; affected user, system, or decision context when relevant>

## In scope
<Included behavior>

## Out of scope
<Non-goals and explicit exclusions that matter>

## Constraints and assumptions
<Consequential constraints and assumptions; distinguish confirmed facts from assumptions>

## Acceptance criteria
- AC-1: <observable outcome>
- AC-2: <observable outcome>

## Open questions
<Only unresolved material decisions; omit when empty>
```

Use `READY` when material behavior and scope are resolved. Use `BLOCKED` when a named decision or missing fact prevents dependent work. Otherwise use `DRAFT`.

Acceptance criteria prove the goal is achieved within its constraints. Describe observable outcomes and how to recognize success, not implementation steps.

## Boundaries

This skill does not design the implementation, edit production code, or authorize implementation.

If the user already asked for broader execution and the contract is clear, the main agent may continue within that existing authorization. Do not add a procedural approval stop.

## Multi-agent use

Keep one owner for the spec and user-facing questions. Explorers may gather bounded facts. A separate reviewer may challenge a substantial contract when the runtime genuinely supports independent agents.

Do not call a role switch in the same context independent review.
