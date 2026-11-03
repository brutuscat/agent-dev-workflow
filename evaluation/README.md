# Behavioral evaluation

The harness runs one primary scenario for each of the 23 calibration cases in fresh synthetic Git repositories. It measures behavior using actual Codex CLI sessions, a no-skill control, mechanical checks, and two separate graders. Some cases document additional independent variants; those variants and real-world generalization are not covered by this run.

## Requirements and isolation

- Linux with `bwrap`, Git, Python 3, and Codex CLI on `PATH`.
- File-based Codex login at `$CODEX_HOME/auth.json` (or `~/.codex/auth.json`) and model access to `gpt-6-luna` and `gpt-6.1-terra`.
- Network access to the Codex service and the ability to create user namespaces and pseudo-terminals.

Each session gets a fresh private temporary Codex home. Only the chosen skill and its bundled references are copied for the skill condition; the control has no workflow skill. A private copy of the login file is used and destroyed with the temporary directory. Each command runs inside `bwrap`, with the host filesystem mounted read-only, a private `/tmp`, the user's home and `/workspace` masked, and only that run's temporary directory writable; Codex also uses its workspace-write sandbox. The CLI is asked to disable plugins, apps, and multi-agent features, but the runtime may still expose delegation. Preflight compares both model-visible skill catalogs and requires a successful shell command for each model. Each tested run also checks the recorded model input for the selected skill text, or for its absence in the control. Child-session lineage and reviewer completions are recorded separately from top-level turn contexts. The isolation is intended to prevent accidental access to the source repository and other runs; it is not a security boundary against a hostile system or model.

## Run

```bash
python3 -m unittest evaluation.test_pilot
python3 evaluation/pilot.py --preflight-only
python3 evaluation/pilot.py
```

The default experiment runs 230 tested-agent sessions (23 cases, two conditions, five repetitions) and up to 460 grader sessions. It runs three tasks concurrently, uses seed 42, and stops scheduling new tasks after an infrastructure error. Already running tasks finish and their results remain recorded. Use `--workers 1` to run serially, `--repetitions 1` for a single pass, `--model gpt-6.1-sol --effort medium` for the Sol medium configuration, `--seed N` to choose an order, `--timeout SECONDS` to set the per-session timeout, and `--case 18 --case 21` to select particular cases. `--resume /absolute/path` continues a stopped experiment without rerunning successful sessions and preserves failed attempts. Resuming requires the original harness, fixtures, skills, and CLI version. `--output /absolute/path` selects a new output directory outside this repository; by default results go under `~/agent-dev-workflow-evaluations/`.

Use `--held-out` with `conditional-questions`, `invoice-no-access`, `invoice-access`, `greenfield-plan`, `existing-plan`, or `self-review` for a separate held-out scenario. These are not included in the default 23-case schedule. Use `--condition skill` or `--condition control` to select one condition.

Case 9 and the invoice follow-up scenarios use two turns in the same session: the original request and a scripted clarification. The runner checks that both turns retain workspace-write sandbox permissions. The selected skill is explicitly invoked only in the treatment condition. The remaining task text is the same in both conditions. The baseline comparison therefore measures the combined effect of invoking the selected skill and loading its bundled baseline, not the isolated causal effect of one instruction.

## Inspect and audit

`manifest.json` records the CLI version, source revision and dirty state, requested model/effort, schedule, seed, and timeout. `preflight.json` records connectivity and command-execution checks. Each case directory contains event transcripts, filtered tool-call inputs and outputs for audit, session provenance, turn sandbox metadata, stderr, before/after Git state and file hashes, a blinded grading bundle, grader transcripts and structured verdicts, and `result.json`. Grader input is scrubbed of workflow skill names, but traces can still reveal the condition indirectly. Raw logs are retained separately and known Codex authentication values are redacted; inspect artifacts before sharing.

Read `report.md` for per-case outcomes and the reproducibly selected human-audit list. Audit every grader disagreement and at least one sampled run per case by comparing its raw transcript and snapshots with the rubric in `pilot.py` and the source calibration document. Mechanical disqualifications take precedence; grader disagreement, unavailable evidence, failed sessions, and invalid grader output remain inconclusive. The automated verdict is preliminary until reviewed. Case 21 explicitly grades the documented P1/BLOCKED convention; a no-skill control may identify the same defect without using that convention, so inspect the findings as well as the verdicts.

A five-run comparison is exploratory. Where verdicts are inconclusive, the report gives a range for the difference rather than treating them as failures. These ranges are not confidence intervals, and an observed pass-rate difference is not a statistical significance claim. Do not pool serious failures into an overall average. Expand to held-out variants, the remaining cases, and appropriately authorized real tasks before drawing broader conclusions.

The case 19 rubric accepts an equivalent direct link check. Results from earlier runs that required the supplied checker are not directly comparable. Earlier case 9 resume sessions used a read-only sandbox; compare their outcomes cautiously with runs using the corrected workspace-write resume.

To compare prior saved evidence after a rubric correction, run `python3 evaluation/regrade.py --source luna=/path/to/luna --source sol=/path/to/sol --case 8 --case 12 --case 14 --case 19 --output /absolute/new/path`. This creates new grader records without changing the original experiment. Filtered tool-call inputs are retained for human audit; they are not included in the blinded automated grading bundle.

Case 8 requires an unavailable subagent API, but the current runtime can expose delegation despite the disabled feature flag. Its scenario verdict is therefore inconclusive unless a concrete read-only violation is demonstrated; attribution grades and session evidence remain available separately. Empty wait events are not proof that no reviewer existed. The collector can also miss intermediate child messages, so a missing recorded completion alone does not prove that a reviewer sent no result or that a claim was fabricated.
