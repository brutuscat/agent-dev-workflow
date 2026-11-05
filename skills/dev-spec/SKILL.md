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

A clear request does not need an interview. If the intended outcome is still vague after inspection, clarify the observable change, its desired effect, and, when relevant and not established, who should experience or benefit from it. Do this before producing the contract. Do not invent a success target to make the request seem ready.

Group related questions when doing so helps the user. A dependent decision may be asked conditionally with its prerequisite when that is useful and the dependency is clear; otherwise defer it. After each answer, remove decisions made irrelevant and directly ask any newly relevant material questions that need user input. Listing an open question in a draft does not replace asking the user. If a question tool is unavailable or fails, ask in plain text. Honor an explicit request for conditional alternatives. Explain what each answer changes and ground recommendations in available evidence or a stated assumption.

## Produce the contract

Use an existing project convention when one exists. Otherwise write `.agent/specs/<slug>.md`. Use chat-only output when requested. After clarification, update the existing spec and status when writes are available and authorized. If only an inline revision can be provided, identify it as the current contract and state that the on-disk draft remains unchanged.

When a useful draft can be written, record settled decisions while asking about unresolved material details. Leave dependent criteria unresolved and use the appropriate status. If the missing outcome or facts would make a draft misleading or unusable, ask and defer the affected work.

For new exposure of private or personal data, default to withholding it unless an established policy or an authorized decision permits it. Preserve established authorized behavior and requested compatibility. Do not invent ownership or grant permissions: if access cannot be established, stop the affected access work and ask.

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
<Only unresolved material decisions, including conditional notes; omit when empty>
```

Use `READY` when material behavior and scope are resolved. Use `BLOCKED` when a named decision or missing fact prevents dependent work. Otherwise use `DRAFT`.

Acceptance criteria prove the goal is achieved within its constraints. Describe observable outcomes and how to recognize success, not implementation steps.

Before marking the spec `READY`, check that acceptance criteria do not require incompatible outcomes when their conditions overlap.

For non-trivial behavior changes, check realistic boundary or failure scenarios for missing observable behavior before marking the spec `READY`. Use the request and repository evidence, not speculation. Cover established outcomes in acceptance criteria; record unresolved material decisions using the question and deferral rules above, and apply the status rules above.

Do not turn an unconfirmed material boundary behavior into an acceptance criterion merely by labeling it an assumption. Use the privacy default above where applicable; otherwise ask when the missing decision changes the contract.

## Boundaries

This skill does not design the implementation, edit production code, or authorize implementation.

If the user already asked for broader execution and the contract is clear, the main agent may continue within that existing authorization. Do not add a procedural approval stop.

## Multi-agent use

Keep one owner for the spec and user-facing questions. Explorers may gather bounded facts. A separate reviewer may challenge a substantial contract when the runtime genuinely supports independent agents.

Do not call a role switch in the same context independent review.
