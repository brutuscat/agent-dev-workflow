---
name: dev-code-review
description: "Read-only review of a requested Git diff for bugs, regressions, integration gaps, and material risks. Use before delivery or when the user asks for review. Prioritize reachable defects over style preferences. Review does not authorize edits or Git mutations."
---

# Dev Code Review

Review the actual change against the behavior it is supposed to provide.

Read `references/dev-baseline.md`.

## Establish scope

Inspect repository root, branch, working-tree status, and the requested staged/unstaged/commit diff.

Honor named paths and exclusions. Do not silently include unrelated work.

Untracked files are not in `git diff`; inspect them when they belong to the requested scope.

Read enough callers, definitions, tests, configuration, and generated boundaries to understand changed behavior. Do not read the entire repository by default.

## Review behavior

Use the request and relevant `.agent/` spec, plan, or fix record as the contract.

Trace changed behavior through important transitions and effects. Check:

- incorrect output or error handling;
- missing registration or integration;
- save/restore and state transitions;
- authorization, sensitive data, integrity, concurrency, and resource lifetime when relevant;
- tests that cannot detect the claimed behavior;
- compatibility or migration gaps;
- unrelated changes that alter delivery scope.

Load `references/risk-checklist.md` only when the diff touches those boundaries.

Project linters and local conventions govern style. Style preference alone is not a defect.

## Findings

Use priorities only when they help the reader:

- **P0** — critical compromise, severe data loss, or unconditional release-wide failure.
- **P1** — high-impact reachable defect that should block delivery.
- **P2** — concrete lower-impact defect or important coverage/integration gap.
- **P3** — optional polish; omit unless useful.

Every finding needs:

- verified location;
- trigger or condition;
- consequence;
- smallest useful correction.

Mark uncertainty instead of overstating it. Do not call a search miss proof that code is dead or unreachable.

## Result

Lead with findings ordered by severity. Then state meaningful verification gaps and the reviewed scope.

Use:

- `BLOCKED` when P0/P1 findings remain;
- `READY` when no blocking finding remains in the reviewed scope;
- `INCOMPLETE` when missing context prevents a responsible result.

`READY` is not proof that tests ran or production works.

A review-only request stays read-only. If fixes were already authorized, return findings to the implementation lane and review the resulting diff again.

## Multi-agent use

Independent review should use an agent that did not author the implementation when the runtime supports it.

Give the reviewer the source contract and actual diff, not the author's preferred conclusion. If no separate reviewer exists, perform a self-review and label it accurately.
