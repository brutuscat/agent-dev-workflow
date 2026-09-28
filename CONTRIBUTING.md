# Contributing

Keep contributions small enough to understand in one review.

Before opening a pull request:

1. Read `AGENTS.md` and the skill or document you are changing.
2. Explain the behavior or ambiguity the change fixes.
3. Keep unrelated cleanup out of the diff.
4. Run:

```bash
bash scripts/validate-repo.sh
bash scripts/test.sh
```

If a script or executable behavior changes, add or update the focused regression case that proves it.

For skill changes, prefer a concrete failure case over adding more general advice. Update `references/calibration-cases.md` when a new rule exists because an agent made a repeatable mistake.

A pull request should state the problem, the change, and the evidence. Long templates are not required.
