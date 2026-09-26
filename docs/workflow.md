# Workflow

Agent Dev Workflow separates coding work into a few responsibilities so an agent does not blur planning, implementation, verification, review, and Git delivery into one optimistic answer.

The phases are optional. Use only the ones that reduce uncertainty or risk.

## Feature path

```text
dev-spec -> dev-plan? -> dev-tdd -> dev-verify -> dev-code-review -> dev-finish
```

Use `dev-spec` when behavior, scope, or acceptance is not already explicit. Use `dev-plan` when implementation choices, ordering, migration, compatibility, security, or recovery risk justify a plan. A small, clear change can start at `dev-tdd`.

## Bug path

```text
dev-fix -> dev-verify -> dev-code-review -> dev-finish
```

`dev-fix` owns reproduction, root-cause tracing, the fix, and regression evidence. Do not add a second TDD phase just because the normal feature path contains one.

## Handoff contracts

Each phase consumes evidence and produces a narrower contract for the next phase.

| Phase | Consumes | Produces |
|---|---|---|
| `dev-spec` | Request, code, docs, known constraints | Scope and observable acceptance criteria |
| `dev-plan` | Spec or clear request, repository structure | Ordered implementation and verification plan |
| `dev-tdd` | Known behavior | Focused test evidence and implementation |
| `dev-fix` | Symptom and expected behavior | Reproduction, cause, fix, regression evidence |
| `dev-verify` | Final relevant state | Commands and observations supporting completion claims |
| `dev-code-review` | Intended behavior and actual diff | Actionable findings or a bounded clean review |
| `dev-finish` | Verified/reviewed scope and explicit Git intent | Exact delivery result |

A file existing is not proof that its contents are current or approved. Read the relevant status and evidence.

## Artifact defaults

Use existing project conventions when they exist. Otherwise use:

```text
.agent/specs/<slug>.md
.agent/plans/<slug>.md
.agent/fixes/<slug>.md
```

Artifacts are coordination tools, not bureaucracy. A small task can keep its contract in the conversation.

Specs use:

- `DRAFT` — useful but not yet ready for dependent implementation.
- `READY` — material behavior and scope are resolved.
- `BLOCKED` — a named decision or missing fact prevents dependent work.

Plans use the same three statuses. A plan is `READY` when its open technical decisions are resolved; that does not authorize implementation.

Fix records use:

- `DIAGNOSED` — root cause is supported but no fix was requested or completed.
- `FIXED` — the scoped fix exists with relevant evidence.
- `BLOCKED` — a concrete missing decision, access requirement, or reproduction gap prevents progress.

## Acceptance criteria

Use observable outcomes, not implementation instructions.

Good:

```text
AC-1: When the token is expired, the API returns 401 and does not call the protected handler.
```

Weak:

```text
AC-1: Add an if statement that checks the token.
```

Stable `AC-*` identifiers are useful when a plan, worker, verifier, and reviewer need to refer to the same behavior.

## Evidence rules

- Prefer a failing proof before a behavior fix when practical.
- Test the real boundary, not a copy of the implementation.
- Use focused checks for local changes and broader checks for shared contracts.
- Distinguish local tests from browser, device, staging, or production evidence.
- Reuse evidence when the tested state has not changed.
- Missing hardware, credentials, or environment access narrows the claim; it does not justify pretending an equivalent check ran.

## Drift

If implementation changes the agreed behavior, update the contract or report the drift before review.

If a bug investigation reveals a larger design change, stop smuggling the refactor into the fix. Move the design decision into `dev-plan`.

The goal is simple: future agents should be able to tell what was intended, what changed, and what evidence supports it.
