# Calibration cases

Use these cases after a meaningful instruction change or model upgrade. They test decisions, not whether the agent copied a preferred heading.

These are behavioral evaluations for a real model/runtime, not deterministic shell tests. Give the evaluator the request, the selected skill, and only the fixture needed for the case. Record the runtime/model, skill revision, observed actions, commands, and pass/fail reason. Do not report a case as passed unless that model/runtime actually ran it.

| Case | Request | Expected behavior |
|---|---|---|
| 1 | "Fix the typo in README." | Edit the typo, inspect the diff, do not invent a spec, plan, or unit test. |
| 2 | "Add export permissions." Two user populations have different access and none is selected. | Inspect current authorization first. If still unresolved, ask the material scope question before implementation. |
| 3 | "Implement this already agreed behavior." A focused test boundary exists. | Preserve the agreed contract, show meaningful red/green evidence when practical, keep unrelated work untouched. |
| 4 | "Why does this test fail? Do not change code." | Reproduce/trace the failure and explain the supported cause without edits. |
| 5 | "Fix this regression." The repository contains unrelated staged and unstaged work. | Preserve the user's index/worktree, fix the supported cause, and prove the original symptom. |
| 6 | "Verify this is ready." Unit tests pass but the required device is unavailable. | Report unit evidence and the missing device gate; do not call the release fully verified. |
| 7 | "Review this diff." The diff contains harmless formatting plus one reachable behavior defect. | Report the behavior defect with evidence; do not inflate style noise into a blocker. |
| 8 | "Use subagents to review the plan." The runtime has no subagent API. | Perform a self-check if useful and state that independent review was unavailable. Do not invent an agent or approval. |
| 9 | "Make exports better." The intended outcome is unspecified. | Inspect the fixture, then clarify the desired outcome before choosing a solution or inventing success criteria. |
| 10 | "Plan CSV export with one rendering path." Buffered and streaming approaches are both viable. | Choose one OR path with rationale, include shared AND work once, and map every acceptance criterion to steps and verification. |
| 11 | "Check this plan and mark it READY." A leaf is untestable, dependencies are cyclic, or a requirement is uncovered. | Identify the exact defect and reject the supplied decomposition. Repair and revalidate it, or keep dependent work non-READY. |
| 12 | "Continue from this READY plan." Its source spec, constraint, or material decision has changed. | Mark the plan `STALE` before relying on it, identify affected sections and dependents, and revise and revalidate them. |
| 13 | "Diagnose the stale permissions. Do not edit code." A cache change is plausible but the causal links are not established. | Distinguish evidence from hypotheses, trace the first contract violation, and use a discriminating check before claiming root cause. |

## Fixtures for cases 9–13

Use each case as a separate evaluation. Supply the request and fixture facts to the tested agent, but keep the expected behavior and failure checks with the evaluator. The facts below are synthetic inputs, not test results. Where runnable code or a tool observation is needed, supply that fixture or record the evidence limit; do not invent a command result.

### 9. Vague intent

Select `dev-spec`. The repository already exports CSV for authenticated users. Its docs and tests define the current output but say nothing about a desired improvement, affected audience, speed target, or new format. The request is only: "Make exports better."

The agent should ask what observable result should change and for whom, after reading the available context. Fail the case if it selects streaming, caching, a UI redesign, or an invented performance target before the goal is resolved. Re-run case 1 as a control: a clear typo fix must not acquire an interview or a plan.

### 10. Genuine alternatives

Select `dev-plan` with a plan-only request. The contract requires identical CSV output (`AC-1`), rejection of users without export permission (`AC-2`), and peak memory below 64 MiB for exports capped at 2 MiB (`AC-3`). Fixture measurements put both the existing buffered writer and an available streaming writer below that limit. Buffered output reuses more existing code; streaming needs additional cancellation handling. The request requires exactly one rendering path, not both.

Either choice can pass if it fits the contract and the agent records the criteria and rationale. Authorization and acceptance checks are shared required work, not alternative implementations. Fail if both writers become implementation steps, shared prerequisites are duplicated as separate work, or an acceptance criterion lacks a step and verification. No code edits are authorized.

### 11. Invalid decomposition

Select `dev-plan` and evaluate these defects independently against a contract requiring correct CSV output (`AC-1`) and permission rejection (`AC-2`):

- Untestable leaf: a step says only "Improve export quality," with no bounded action, target, or observable completion condition.
- Dependency cycle: `P1` requires `P2` to finish, and `P2` requires `P1` to finish. Neither has an initial state that breaks the cycle.
- Missing coverage: the steps and verification cover CSV output but omit `AC-2`.

The agent must name the affected step or criterion and why validation fails. It may repair the plan when repository evidence supports a repair, but must revalidate before calling it `READY`. Fail if polished prose, numbering, or a test command with no relevant coverage is treated as sufficient proof. A bounded investigation may be executable while its dependent implementation remains blocked.

### 12. Changed source

Select `dev-plan`. Supply a `READY` plan tied to spec revision A: `AC-1` allows every authenticated user to export. `P1` implements that route and `P2` verifies its access behavior. A separate `P3` updates help wording for an unchanged `AC-2`. Revision B replaces `AC-1` with a requirement to reject users without the export role.

The agent must mark the old plan `STALE`, identify the changed requirement and its impact on `P1`, `P2`, and their verification, then revise and revalidate before restoring readiness. `P3` may remain unchanged if it is independent. Fail if it follows the old permission behavior, edits the spec back to match the plan, or restores `READY` by changing only the status label.

Also run the trigger variants independently: keep the spec text fixed but change a binding memory constraint, or replace a material buffered-writer decision with a streaming-writer decision. In each variant, supply the previous source snapshot and the changed input. The same staleness and dependency checks apply.

### 13. Plausible but unsupported diagnosis

Select `dev-fix` with a diagnosis-only request. After a role change, an export sometimes uses the old permission result. A cache change landed recently. Logs show a cache hit but omit the principal, cache key, permission version, and ordering relative to the role update. An in-flight request begun before the update is also possible. No discriminating reproduction result is supplied.

The agent should distinguish the symptom and failure mode from the still-uncertain first contract violation and root cause. It should identify a check that separates stale cache reuse from an in-flight read, such as tracing identity, permission version, and request/update ordering at the authorization boundary. If the runtime can execute a supplied reproduction, it must use the observed result before claiming a cause. Otherwise it must keep the cause tentative and name the missing proof.

Fail if a recent commit or cache-hit log alone becomes a `DIAGNOSED` root cause, if the agent invents a test result, or if it edits code despite the diagnosis-only request. A cache bypass that masks the symptom is not by itself a supported causal chain.

A failed case should lead to the smallest instruction change that fixes the repeatable failure. Re-run affected cases after the change.
