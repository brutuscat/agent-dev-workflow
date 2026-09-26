# Calibration cases

Use these cases after a meaningful instruction change or model upgrade. They test decisions, not whether the agent copied a preferred heading.

Give the evaluator the request, the selected skill, and only the fixture needed for the case. Record the runtime/model, skill revision, observed actions, commands, and pass/fail reason.

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

A failed case should lead to the smallest instruction change that fixes the repeatable failure. Re-run affected cases after the change.
