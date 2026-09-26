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
