#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/agent-dev-workflow-validate-tests.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

EXPECTED_SKILLS=(dev-auto dev-spec dev-plan dev-tdd dev-fix dev-verify dev-code-review dev-finish)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_contains() { grep -Fq -- "$2" "$1" || fail "expected '$2' in $1"; }

make_repo() {
  local dir="$1"
  mkdir -p "$dir"/{scripts,tests,references,skills,docs,assets,.codex-plugin}
  cp "$ROOT/scripts/validate-repo.sh" "$dir/scripts/"
  cp "$ROOT/scripts/validate-skill-package.sh" "$dir/scripts/"
  cp "$ROOT/scripts/install-codex-skills.sh" "$dir/scripts/"

  cat > "$dir/scripts/test.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
SH
  cat > "$dir/tests/test-install-codex-skills.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
SH
  cat > "$dir/tests/test-validate-repo.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
SH
  chmod +x "$dir/scripts/"*.sh "$dir/tests/"*.sh

  printf '# baseline\n' > "$dir/references/dev-baseline.md"
  printf '# Calibration cases\n' > "$dir/references/calibration-cases.md"
  printf '# Workflow\n' > "$dir/docs/workflow.md"
  printf '# Multi-agent\n' > "$dir/docs/multi-agent.md"
  printf '# AGENTS\n' > "$dir/AGENTS.md"
  printf '<svg/>\n' > "$dir/assets/logo.svg"
  printf '<svg/>\n' > "$dir/assets/icon.svg"

  cat > "$dir/README.md" <<'MD'
# Fixture
[workflow](docs/workflow.md)
[multi-agent](docs/multi-agent.md)
![logo](assets/logo.svg)
[agents](AGENTS.md)
MD

  cat > "$dir/.codex-plugin/plugin.json" <<'JSON'
{
  "name": "agent-dev-workflow",
  "repository": "https://github.com/brutuscat/agent-dev-workflow",
  "skills": "./skills/",
  "interface": {
    "composerIcon": "./assets/icon.svg",
    "logo": "./assets/logo.svg"
  }
}
JSON

  local skill
  for skill in "${EXPECTED_SKILLS[@]}"; do
    mkdir -p "$dir/skills/$skill/references"
    cat > "$dir/skills/$skill/SKILL.md" <<SKILL
---
name: $skill
description: "Fixture for $skill."
version: 1.0.0
---

# $skill
Read \`references/dev-baseline.md\`.
SKILL
    cp "$dir/references/dev-baseline.md" "$dir/skills/$skill/references/dev-baseline.md"
  done

  mkdir -p "$dir/skills/dev-auto/agents"
  cat > "$dir/skills/dev-auto/agents/openai.yaml" <<'YAML'
interface:
  display_name: "Dev Auto"
policy:
  allow_implicit_invocation: false
YAML

  cat >> "$dir/skills/dev-code-review/SKILL.md" <<'MD'
Load `references/risk-checklist.md` when relevant.
MD
  printf '# risk\n' > "$dir/skills/dev-code-review/references/risk-checklist.md"

  git -C "$dir" init -q -b master
  git -C "$dir" config user.name test
  git -C "$dir" config user.email test@example.invalid
  git -C "$dir" add .
  git -C "$dir" commit -qm baseline
}

run_validator() {
  local dir="$1" log="$2"
  shift 2
  (cd "$dir" && unset VALIDATE_BASE_SHA VALIDATE_HEAD_SHA && "$@" bash scripts/validate-repo.sh) >"$log" 2>&1
}

expect_fail() {
  local dir="$1" log="$2"
  shift 2
  if run_validator "$dir" "$log" "$@"; then
    cat "$log" >&2
    fail "validator unexpectedly passed: $dir"
  fi
}

copy_case() {
  local name="$1"
  local dest="$TMP/$name"
  cp -R "$TMP/base" "$dest"
  printf '%s\n' "$dest"
}

echo "[validate] clean package with optional scalar metadata passes"
make_repo "$TMP/base"
run_validator "$TMP/base" "$TMP/base.log" env
assert_contains "$TMP/base.log" "Validation OK"

echo "[validate] malformed YAML-like required scalar fails"
case_dir="$(copy_case malformed)"
tmp_file="$case_dir/skills/dev-plan/SKILL.md.tmp"
sed 's/^description:.*/description: "unterminated/' "$case_dir/skills/dev-plan/SKILL.md" > "$tmp_file"
mv "$tmp_file" "$case_dir/skills/dev-plan/SKILL.md"
expect_fail "$case_dir" "$TMP/malformed.log" env
assert_contains "$TMP/malformed.log" "malformed quoted description"

echo "[validate] missing frontmatter delimiters fails"
case_dir="$(copy_case no-frontmatter)"
tmp_file="$case_dir/skills/dev-spec/SKILL.md.tmp"
awk 'NR != 1 && NR != 4' "$case_dir/skills/dev-spec/SKILL.md" > "$tmp_file"
mv "$tmp_file" "$case_dir/skills/dev-spec/SKILL.md"
expect_fail "$case_dir" "$TMP/no-frontmatter.log" env
assert_contains "$TMP/no-frontmatter.log" "must start with YAML frontmatter"

echo "[validate] empty description fails"
case_dir="$(copy_case empty-description)"
tmp_file="$case_dir/skills/dev-tdd/SKILL.md.tmp"
sed 's/^description:.*/description: ""/' "$case_dir/skills/dev-tdd/SKILL.md" > "$tmp_file"
mv "$tmp_file" "$case_dir/skills/dev-tdd/SKILL.md"
expect_fail "$case_dir" "$TMP/empty-description.log" env
assert_contains "$TMP/empty-description.log" "empty description"

echo "[validate] missing baseline copy fails"
case_dir="$(copy_case missing-baseline)"
rm "$case_dir/skills/dev-verify/references/dev-baseline.md"
expect_fail "$case_dir" "$TMP/missing-baseline.log" env
assert_contains "$TMP/missing-baseline.log" "baseline copy missing"

echo "[validate] missing explicit-only invocation policy fails"
case_dir="$(copy_case missing-policy)"
rm "$case_dir/skills/dev-auto/agents/openai.yaml"
expect_fail "$case_dir" "$TMP/missing-policy.log" env
assert_contains "$TMP/missing-policy.log" "explicit invocation policy missing"

echo "[validate] missing referenced resource fails"
case_dir="$(copy_case missing-reference)"
rm "$case_dir/skills/dev-code-review/references/risk-checklist.md"
expect_fail "$case_dir" "$TMP/missing-reference.log" env
assert_contains "$TMP/missing-reference.log" "references missing resource"

echo "[validate] nonexistent plugin skills path fails"
case_dir="$(copy_case plugin-path)"
node - "$case_dir/.codex-plugin/plugin.json" <<'NODE'
const fs = require('fs');
const p = process.argv[2];
const data = JSON.parse(fs.readFileSync(p, 'utf8'));
data.skills = './does-not-exist/';
fs.writeFileSync(p, JSON.stringify(data, null, 2) + '\n');
NODE
expect_fail "$case_dir" "$TMP/plugin-path.log" env
assert_contains "$TMP/plugin-path.log" "plugin skills path must resolve to the repository skills directory"

echo "[validate] staged whitespace fails"
case_dir="$(copy_case staged-whitespace)"
printf 'bad trailing space   \n' >> "$case_dir/README.md"
git -C "$case_dir" add README.md
expect_fail "$case_dir" "$TMP/staged-whitespace.log" env
assert_contains "$TMP/staged-whitespace.log" "trailing whitespace"

echo "[validate] committed range whitespace fails"
case_dir="$(copy_case committed-whitespace)"
base_sha="$(git -C "$case_dir" rev-parse HEAD)"
printf 'bad committed space   \n' >> "$case_dir/README.md"
git -C "$case_dir" add README.md
git -C "$case_dir" commit -qm bad-whitespace
head_sha="$(git -C "$case_dir" rev-parse HEAD)"
expect_fail "$case_dir" "$TMP/committed-whitespace.log" env VALIDATE_BASE_SHA="$base_sha" VALIDATE_HEAD_SHA="$head_sha"
assert_contains "$TMP/committed-whitespace.log" "trailing whitespace"

printf 'Validator regression tests passed\n'
