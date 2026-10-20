---
name: dev-verify
description: "Verify implemented work before claiming it is complete, fixed, passing, or ready. Match evidence to the requested behavior and risk, inspect actual command results, and state missing proof. Verification is read-only unless the user explicitly reassigns implementation work."
---

# Dev Verify

Make the completion claim no broader than the evidence.

Read `references/dev-baseline.md`.

## Define the claim

Start from the request and relevant spec, plan, or fix record. Identify what must be true and the smallest sufficient proof.

Examples:

| Claim | Useful proof |
|---|---|
| Behavior implemented | Test or direct check of the acceptance criteria |
| Bug fixed | Original reproduction or faithful regression passes |
| Refactor preserved behavior | Relevant characterization tests pass |
| Build/lint succeeds | The actual project command completes successfully |
| Browser/device behavior works | The relevant rendered state and interaction on that environment |
| Docs/skill changed correctly | Structure/link checks plus content review |

Use focused checks for local changes and broader checks for shared contracts or high-risk boundaries.

## Run and inspect

Use evidence from the final relevant state.

Record exact commands, exit status, and meaningful output. Inspect failures, skips, and warnings that change the claim.

Do not treat a worker's summary as proof without inspecting the relevant output or rerunning the critical check.

Keep verification read-only with respect to source and Git staging. If a problem needs a code change, report it and return the task to an implementation lane unless the user explicitly asks the verifier to fix it.

Unavailable hardware, credentials, services, or tooling limit the claim. Finish feasible checks and state the missing gate.

## Report

For small work, a short result is enough.

For substantial work, evaluate each required acceptance criterion (or each important requirement when no criteria are defined) against evidence from the final relevant state:

- `PASS` — sufficient evidence demonstrates the outcome.
- `FAIL` — observed behavior contradicts the outcome.
- `UNVERIFIED` — evidence is missing or inconclusive; name the missing check.

Report each criterion's verdict and supporting evidence. For `FAIL`, name the observed failure and the next diagnostic or corrective action. For `UNVERIFIED`, name the smallest feasible check needed to resolve the gap. Keep residual risks separate. Do not claim full completion while any required criterion is `FAIL` or `UNVERIFIED`.

Verification does not replace code review and does not authorize Git delivery.

## Multi-agent use

This is a strong read-only delegation target. Give the verifier the current task contract, exact snapshot/scope, and required claims.

A genuinely separate verifier is independent. A role switch in the author's context is a self-check and should be described that way.
