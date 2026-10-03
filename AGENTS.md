# Instructions for Agent Dev Workflow

This repository is built for coding agents, but every change still needs to be understandable and defensible by a human reviewer.

## Working rules

1. **Read before writing.** Inspect the affected skill, nearby references, validation rules, and current repository state before changing behavior.
2. **Keep scope narrow.** Change only what the task requires. Do not bundle unrelated cleanup, new abstractions, or formatting churn.
3. **Preserve existing work.** Do not stash, reset, overwrite, or discard unrelated user changes. Dirty state is information, not a reason to erase work.
4. **Use strong contracts at boundaries.** Make inputs, outputs, ownership, failure behavior, and stop conditions explicit when ambiguity could change execution.
5. **Prefer repository conventions.** Existing code, tests, linters, and project configuration beat generic style advice.
6. **Verify before claiming success.** Run the checks that prove the requested behavior. State what did not run and what that limits.
7. **Keep review separate from authorship.** A self-check is useful, but it is not independent review.
8. **Keep Git authority explicit.** A request to edit does not imply commit, push, merge, force-push, or destructive cleanup.

## Writing instructions

Use the smallest clear wording that preserves intent, uncertainty, constraints, identifiers, and technical terms.

- Put a condition next to the action it controls.
- Use one stable term for one concept.
- Split instructions when combining them creates multiple execution paths.
- Keep `must`, `should`, `may`, and `can` distinct.
- State failure and recovery behavior when it matters.
- Do not invent missing behavior to make a document look complete.

For ambiguous agent instructions, apply the principles from the `agent-clarity` skill before expanding the text.

## Skill changes

A skill should answer four questions quickly:

- When should it run?
- What does it own?
- What evidence or artifact does it produce?
- Where does its authority stop?

Do not add a new skill when an existing skill can own the behavior without becoming ambiguous. Do not make skills call each other through a hidden chain.

Default workflow artifacts use `.agent/` paths. Keep those paths and status words consistent across skills and docs.

## Multi-agent changes

The main agent owns decomposition, user communication, integration, Git mutations, and the final result.

Delegate only bounded work with explicit read/write scope and a verifiable output. Two workers must not edit the same files concurrently. A verifier or reviewer should not inherit the author's conclusion as evidence.

See `docs/multi-agent.md`.

## Validation

Run before proposing a repository change:

```bash
bash scripts/validate-repo.sh
bash scripts/test.sh
```

If executable behavior changes, add or update the narrow regression case that proves it. Report failures instead of weakening the checks to make the change pass.

## Documentation map

- `README.md` — what the project is and how to use it.
- `docs/workflow.md` — phase and artifact contracts.
- `docs/multi-agent.md` — delegation and ownership rules.
- `references/dev-baseline.md` — shared baseline copied into each skill.
- `references/calibration-cases.md` — behavioral cases for instruction changes.
