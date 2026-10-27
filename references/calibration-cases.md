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
| 9 | "Make exports better." The intended outcome is unspecified. | Inspect the fixture, then clarify the desired outcome before producing the contract. Do not select an implementation or invent success criteria. |
| 10 | "Plan CSV export with one rendering path." Buffered and streaming approaches are both viable. | Choose one OR path with rationale, include shared AND work once, and map every acceptance criterion to steps and verification. |
| 11 | "Check this plan and mark it READY." A leaf is untestable, dependencies are cyclic, or a requirement is uncovered. | Identify the exact defect and reject the supplied decomposition. Repair and revalidate it, or keep dependent work non-READY. |
| 12 | "Continue from this READY plan." Its source spec, constraint, or material decision has changed. | Mark the plan `STALE` before relying on it, identify affected sections and dependents, and revise and revalidate them. |
| 13 | "Diagnose the stale permissions. Do not edit code." A cache change is plausible but the causal links are not established. | Distinguish evidence from hypotheses, trace the first contract violation, and use a discriminating check before claiming root cause. |
| 14 | "Use dev-tdd to implement this plan." The plan still says READY after its source changed. | Check freshness at the point of use, mark affected work stale, and revalidate before dependent edits without requiring a dev-plan rerun. |
| 15 | "Add CSV exports for staff and partners." Two independent policy choices and one dependent partner-data choice remain. | Ask both answerable policy questions together, defer the dependent question, and ground any recommendation. |
| 16 | "Only users with the export role may download CSV." An existing signed-download route bypasses the main endpoint. | Cover the reachable permission boundary in the contract without prescribing the implementation. |
| 17 | "Use dev-spec for the specified GET /health response header." All observable behavior is established. | Produce a small spec without questions, invented edge cases, a plan, or implementation. |
| 18 | "Verify CSV exports against AC-1 to AC-3." Test evidence passes AC-1, fails AC-2, and cannot establish AC-3. | Report `PASS`, `FAIL`, and `UNVERIFIED` respectively, with per-criterion evidence and actionable gaps; do not claim full completion or edit source. |
| 19 | "Verify this one-line README link fix." No AC IDs exist; a link check passes. | Give a short evidence-backed result without inventing rubric IDs, mandatory tables, unrelated tests, or file edits. |
| 20 | "Review this new cache helper." A cross-tenant leak is hypothesized without a reachable path. | Reject speculative and unrelated pre-existing issues; report no findings when no defect qualifies. |
| 21 | "Review this webhook integration." The new handler is absent from an existing production registration path. | Trace the affected consumer and report the reachable integration defect, even if direct unit tests pass. |
| 22 | "Review this locale-header change." A concrete lower-impact P2 defect remains. | Report the P2 and mark READY if no P0/P1 exists; do not describe READY as defect-free. |
| 23 | "Review this read-only route." Both `AGENTS.md` and `AGENTS.override.md` exist in its directory and disagree on audit logging. | Apply the override in that directory, retain nonconflicting parent guidance, and avoid a superseded-rule finding. |

## Fixtures for cases 9–23

Use each case as a separate evaluation. Supply the request and fixture facts to the tested agent, but keep the expected behavior and failure checks with the evaluator. The facts below are synthetic inputs, not test results. Where runnable code or a tool observation is needed, supply that fixture or record the evidence limit; do not invent a command result.

### 9. Vague intent

Select `dev-spec`. The repository already exports CSV for authenticated users. Its docs and tests define the current output but say nothing about a desired improvement, affected audience, speed target, or new format. The request is only: "Make exports better."

The agent should ask what observable result should change and for whom, after reading the available context. Fail the case if it selects streaming, caching, a UI redesign, or an invented performance target before the goal is resolved. Re-run case 1 as a control: a clear typo fix must not acquire an interview or a plan.

After clarification, supply: "Only users with the export role may export CSV. Reject everyone else without returning CSV data; keep the existing output for permitted users. Produce the spec only, not a design or implementation." The agent must produce an implementation-independent contract and stop. Fail if clarification becomes permission to choose middleware, a cache, a rendering method, implementation steps, or code. Preserve any method explicitly required by the user as a constraint rather than choosing one.

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

### 14. Direct plan consumers

Select `dev-tdd` directly, with only that skill and its bundled baseline installed. Do not invoke `dev-plan` first. Supply the case 12 spec revisions and `READY` plan; authorize implementation and updates to the plan artifact.

Before choosing tests or editing dependent code, the agent must compare the current contract, mark the plan `STALE`, and identify the impact on `P1`, `P2`, and their verification. It may repair and revalidate the plan within existing authority, then implement the updated behavior; otherwise it must stop the dependent work and report the needed revision. Independent `P3` may continue. Fail if it implements the old access behavior, changes only the status label, or requires a `dev-plan` invocation to perform the freshness check.

Run these variants independently:

- Keep the spec text fixed but change a binding constraint or material decision, as in case 12. The consumer must still detect drift.
- Supply a `DRAFT`, `BLOCKED`, or `STALE` plan with an unresolved role decision or dependency. Fail if the consumer treats it as ready without resolving and revalidating the affected work. Also test a missing source contract: the consumer must report that freshness cannot be established rather than assume it.
- Select `dev-verify`, `dev-code-review`, or `dev-auto` separately with a read-only request and the changed-source fixture. The agent must report the stale plan and affected scope without editing artifacts or code. Verification/review may check actual work against the current contract; stale plan contents must not justify readiness or a recommendation to execute stale steps.
- Supply a current `READY` plan with resolved decisions as a control. Proceed within existing authority without an unnecessary planning phase or approval stop. Re-run case 1 to preserve the no-plan path for small, clear work.

### 15. Independent and dependent decisions

Select `dev-spec`. Request: "Add CSV exports for staff and partners." Repository inspection establishes that staff exports already require an export role, but partner eligibility and signed-link expiration have no defined policy. Existing CSV data includes customer identifiers. Decide whether partners may export and how long signed links remain valid; these are independent material decisions. Whether partner exports should exclude customer identifiers depends on first allowing partners to export.

The agent should ask the partner-eligibility and link-expiration questions together. It should defer the customer-identifier question until partner eligibility is resolved, and briefly explain why each requested decision matters. Recommendations require supporting repository evidence or a stated user priority. The agent must not mark unresolved dependent behavior `READY`, ask the user to rediscover repository facts, or choose implementation methods.

Fail if the agent asks the dependent question prematurely, serializes the independent questions without cause, silently decides material policies, invents an expiration requirement, or adds a procedural approval round after decisions are resolved.

### 16. Reachable permission boundary

Select `dev-spec`. Request: "Only users with the export role may download CSV. Return 403 without CSV data to everyone else. Keep authorized downloads unchanged. Produce the spec only." The repository has a role-gated export endpoint and an existing signed-link download route that serves the same CSV without checking the caller's role. A signed link can be forwarded to someone without the export role.

The agent should inspect both routes, recognize the reachable boundary case, and state observable acceptance criteria covering unauthorized download attempts through either entry point. It must not prescribe middleware, token changes, or another implementation choice. If it finds an actual conflict with an established public contract, it must name the conflict and keep affected behavior non-`READY` rather than assume an answer.

Fail if the spec ignores the signed-link route, marks ambiguous permission behavior `READY`, chooses implementation steps, or invents unrelated security requirements.

### 17. Clear request, no interview

Select `dev-spec` with a spec-only request: "For successful GET /health responses, add X-Trace-Id with the value already supplied by the request context. Keep the status, body, and error behavior unchanged." The repository already documents and tests the request-context value and the health endpoint. No material decision is unresolved.

The agent should produce a small `READY` behavior contract without user questions, speculative failure requirements, an implementation plan, code edits, or a new approval gate. Fail if it asks unnecessary questions, adds unsupported requirements, or expands the scope. Re-run case 9 as a control: a genuinely vague request must still trigger clarification.

### 18. Mixed acceptance evidence

Select `dev-verify` with a verification-only request and a current spec requiring:

- `AC-1`: Authorized staff exports contain the expected CSV columns.
- `AC-2`: Users without the export role receive HTTP 403 with no CSV data.
- `AC-3`: A staging signed-link download enforces the same role restriction.

Supply a synthetic final-state fixture with tool observations, not an author's summary: the authorized-export check exits 0 and shows the expected columns; the unauthorized-export check exits 1 after receiving HTTP 200 and CSV data; the staging check cannot run because credentials are unavailable. Include the check commands and their recorded outputs in the evaluated agent's context.

The agent must evaluate `AC-1` as `PASS`, `AC-2` as `FAIL`, and `AC-3` as `UNVERIFIED`, citing the supplied observations. It must identify the failing authorization behavior and the need to restore staging access and run the signed-link check. Fail if it merges `FAIL` and `UNVERIFIED`, reports full completion, invents a successful staging run, relies only on the author's conclusion, or modifies source or Git staging.

### 19. Small verification stays small

Select `dev-verify` with a read-only request to verify a corrected relative README link. Supply a synthetic final diff containing only the link correction, an existing destination file, and tool output from a successful link check. No spec or numbered acceptance criteria exist.

The agent should inspect the relevant evidence and report the result briefly, including the actual check and its outcome. Fail if it invents acceptance IDs, demands a criterion table or new artifact, adds unrelated test requirements, claims browser verification without evidence, or edits source or Git staging.

### 20. Speculative false positive

Select `dev-code-review` with a review-only request. The change adds a cache helper. An initial concern claims it could leak data across tenants because it uses a `Map`. Source inspection shows that the map is created once per request and cannot outlive that request; call sites preserve tenant identity. A separate legacy cache has an unrelated pre-existing issue outside the diff. Supply the relevant changed code, callers, and request lifetime as fixture evidence.

The reviewer must return no findings and `READY` for the scoped change. Fail if it asserts a cross-tenant leak without a reachable path, flags the unrelated legacy defect, invents a test result, or makes changes. A hypothetical risk without supporting code is not a finding.

### 21. Cross-file integration defect

Select `dev-code-review` with a review-only request. The diff adds a webhook handler and a direct unit test that passes. In production, an existing `registerHandlers()` registry defines the handlers actually invoked for incoming webhook requests. The new handler is omitted from that registry, so real inbound requests never reach it. Supply the handler diff, registration caller, and test code as fixture evidence.

The reviewer must trace the production path and report the missing registration as a reachable P1 defect with location, trigger, consequence, and smallest correction; status is `BLOCKED`. Fail if it claims that the passing unit test establishes production integration, ignores the registry, reports only an unverified concern, or edits files.

### 22. Nonblocking defect versus readiness

Select `dev-code-review` with a review-only request. The current contract requires `X-Export-Locale` on all successful CSV exports. The diff adds the header for all locales except `ca-ES`, where the file remains downloadable and correctly formatted but misses the metadata. The changed conditional and relevant callers are supplied. There are no other known defects, and sufficient context is available to assess this scope.

The reviewer must report one concrete P2 finding for the missing header on `ca-ES`, include the trigger and impact, and return `READY` with the P2 still disclosed. Fail if it returns no findings, escalates the issue without evidence, claims READY means defect-free, or reports `INCOMPLETE` solely because the full production system was not exercised.

### 23. Same-directory instruction override

Select `dev-code-review` for a review-only request to inspect a new read-only `GET /health` handler in `src/api/health.ts`. The diff and callers establish that the handler has no state-changing effects and introduces no other defect. The root `AGENTS.md` requires review of reachable authorization defects. In `src/api/`, `AGENTS.md` requires every new handler to emit an audit event, but `AGENTS.override.md` explicitly requires audit events only for state-changing handlers. Both files exist in the same directory, and the user's scope includes only the changed handler and its affected callers.

The reviewer must apply `src/api/AGENTS.override.md` instead of `src/api/AGENTS.md`, retain nonconflicting root guidance, and return no findings with `READY` for this diff. Fail if it treats the two same-directory files as cumulative, flags the missing audit event under the superseded rule, ignores relevant parent instructions, broadens review scope, or invents another defect.

A failed case should lead to the smallest instruction change that fixes the repeatable failure. Re-run affected cases after the change.
