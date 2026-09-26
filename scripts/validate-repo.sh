#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EXPECTED_SKILLS=(
  dev-auto
  dev-spec
  dev-plan
  dev-tdd
  dev-fix
  dev-verify
  dev-code-review
  dev-finish
)

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

echo "Checking repository shape..."
for file in \
  README.md \
  AGENTS.md \
  docs/workflow.md \
  docs/multi-agent.md \
  references/dev-baseline.md \
  references/calibration-cases.md \
  assets/logo.svg \
  assets/icon.svg \
  .codex-plugin/plugin.json; do
  [[ -f "$file" ]] || fail "$file missing"
done

mapfile -t actual_skills < <(find skills -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
mapfile -t expected_skills < <(printf '%s\n' "${EXPECTED_SKILLS[@]}" | sort)

[[ "${#actual_skills[@]}" == "${#expected_skills[@]}" ]] || \
  fail "expected ${#expected_skills[@]} skill directories, found ${#actual_skills[@]}"

for i in "${!expected_skills[@]}"; do
  [[ "${actual_skills[$i]}" == "${expected_skills[$i]}" ]] || \
    fail "unexpected skill set: ${actual_skills[*]}"
done

for skill in "${EXPECTED_SKILLS[@]}"; do
  file="skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "$file missing"
  grep -q "^name: $skill$" "$file" || fail "$file has the wrong name"
  grep -q '^description:' "$file" || fail "$file missing description frontmatter"
  [[ -f "skills/$skill/references/dev-baseline.md" ]] || fail "$skill baseline copy missing"
  cmp -s references/dev-baseline.md "skills/$skill/references/dev-baseline.md" || \
    fail "$skill baseline copy drifted"
done

echo "Checking scripts..."
[[ -x scripts/install-codex-skills.sh ]] || fail "installer is not executable"
[[ -x scripts/validate-repo.sh ]] || fail "validator is not executable"
bash -n scripts/install-codex-skills.sh
bash -n scripts/validate-repo.sh

echo "Checking plugin metadata..."
node -e 'JSON.parse(require("fs").readFileSync(".codex-plugin/plugin.json", "utf8"))'
grep -q '"name": "agent-dev-workflow"' .codex-plugin/plugin.json || fail "plugin name is wrong"
grep -q 'brutuscat/agent-dev-workflow' .codex-plugin/plugin.json || fail "plugin repository URL is wrong"

echo "Checking documentation links..."
grep -q 'docs/workflow.md' README.md || fail "README must link workflow docs"
grep -q 'docs/multi-agent.md' README.md || fail "README must link multi-agent docs"
grep -q 'assets/logo.svg' README.md || fail "README must use the repository logo"
grep -q 'AGENTS.md' README.md || fail "README must link repository instructions"

echo "Checking language..."
if grep -RIPq '[\x{4E00}-\x{9FFF}]' README.md AGENTS.md CONTRIBUTING.md docs references skills .codex-plugin; then
  fail "retained documentation must be English"
fi

echo "Checking diff whitespace..."
git diff --check

echo "Validation OK"
