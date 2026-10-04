# Dev Baseline

These rules apply to every skill.

This file is the editing source. Keep each `skills/<skill>/references/dev-baseline.md` copy identical so a skill remains self-contained when installed alone.

## 1. Do not guess material decisions

Read the request, prior decisions, relevant code, tests, and available tools before asking questions.

Ask only when missing information changes user-visible behavior, a public contract, authorization, destructive scope, or another hard-to-reverse choice. Make low-risk reversible choices from project conventions and state assumptions that affect the result.

## 2. Keep the change small

Do only what the task needs. Reuse existing patterns before adding abstractions, dependencies, configuration, or future-facing flexibility.

Scale process to risk. A typo does not need a design document. A migration or authorization change may.

## 3. Preserve existing work

Inspect repository, branch, working tree, and index before writes when Git state matters.

Do not stash, reset, overwrite, reformat, or discard unrelated work. Limit edits to the requested scope and keep every changed line explainable from the task.

## 4. Prove what you claim

Choose checks that demonstrate the requested behavior on the final relevant state.

Report exact commands and meaningful results. Distinguish static checks, unit tests, simulations, browsers/devices, staging, and production evidence. If a required check cannot run, state the missing proof and narrow the claim.

## 5. Check plans before use

Before any skill relies on a plan, read its status and compare its source request/spec, constraints, and material decisions with the current contract. A `READY` label alone does not prove freshness.

If an input changed, treat the plan as `STALE` and identify affected sections and dependent steps/checks. Write that status and impact into the existing plan only when artifact edits are authorized; otherwise report them without editing files.

Do not rely on a `DRAFT`, `BLOCKED`, or `STALE` plan, or one whose freshness cannot be established, for dependent implementation or completion claims. Before relying on affected parts, revise them and revalidate acceptance coverage, dependencies, choices, and feasibility; restore `READY` only when those checks pass and blockers are resolved. Perform repairs only within existing authority; otherwise report the needed revision.

Independent, unaffected work and read-only checks against the current contract may continue within existing authorization. This check does not require a plan for small, clear tasks or an invocation of `dev-plan`.
