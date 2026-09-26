---
name: dev-fix
description: "Investigate a bug, regression, failing test, or broken behavior by reproducing it and tracing evidence to the root cause. Implement the smallest supported fix when requested and prove the original symptom is resolved. Diagnosis-only requests do not authorize edits."
---

# Dev Fix

Find the first point where actual state diverges from the intended contract. Fix the supported cause, not just the visible crash.

Read `references/dev-baseline.md`.

## Establish the failure

Determine:

- observed symptom;
- expected behavior;
- trigger and relevant environment;
- whether the user wants diagnosis only or a fix.

Read available logs, code, tests, recent changes, and configuration before asking for facts the repository can answer.

Inspect Git state before writes. Preserve unrelated work and partial staging.

## Reproduce and trace

Use the smallest faithful reproduction available: a failing test, command, request, trace, or repeatable interaction.

If reproduction is intermittent, prefer deterministic ordering, barriers, fake clocks, or event-based waits over arbitrary sleeps.

Trace the real control/data path backward from the symptom until you find where the contract is first violated. A guard at the crash site is not a root-cause fix when bad state originates earlier.

Use competing hypotheses only when they help discriminate evidence. Do not create a fixed quota of hypotheses or attach fake probabilities.

## Fix and prove

When a fix is requested and the cause is supported:

1. Prefer a regression proof that fails for the original behavior.
2. Change the cause and only the directly required surrounding code.
3. Re-run the original reproduction.
4. Run checks for affected neighboring behavior.
5. Remove temporary instrumentation added for the investigation.

If an automated regression test is not practical, use the strongest feasible evidence and state what remains unverified.

Do not route the same bug through `dev-tdd` afterward. This skill already owns regression evidence.

## Durable record

For a substantial investigation, or when requested, use `.agent/fixes/<slug>.md` with:

- status: `DIAGNOSED`, `FIXED`, or `BLOCKED`;
- symptom and expectation;
- reproduction;
- supported root cause;
- fix;
- commands/results;
- remaining limits.

Small fixes can keep this contract in the final response.

## Multi-agent use

Explorers may trace independent failure paths or gather bounded evidence. A worker may implement a fix when ownership is clear.

The final verifier/reviewer should evaluate the integrated result independently. Do not treat the investigator's confidence as proof.
