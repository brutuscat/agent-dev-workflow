#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

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
  .codex-plugin/plugin.json \
  scripts/install-codex-skills.sh \
  scripts/validate-skill-package.sh \
  scripts/validate-repo.sh \
  scripts/test.sh \
  tests/test-install-codex-skills.sh \
  tests/test-validate-repo.sh; do
  [[ -f "$file" ]] || fail "$file missing"
done

bash scripts/validate-skill-package.sh \
  --skills-dir "$ROOT/skills" \
  --baseline "$ROOT/references/dev-baseline.md"

echo "Checking scripts..."
for script in \
  scripts/install-codex-skills.sh \
  scripts/validate-skill-package.sh \
  scripts/validate-repo.sh \
  scripts/test.sh \
  tests/test-install-codex-skills.sh \
  tests/test-validate-repo.sh; do
  [[ -x "$script" ]] || fail "$script is not executable"
  bash -n "$script"
done

echo "Checking plugin metadata..."
node <<'NODE'
const fs = require('fs');
const path = require('path');

const root = process.cwd();
const pluginPath = path.join(root, '.codex-plugin', 'plugin.json');
const plugin = JSON.parse(fs.readFileSync(pluginPath, 'utf8'));

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

if (plugin.name !== 'agent-dev-workflow') fail('plugin name is wrong');
if (plugin.repository !== 'https://github.com/brutuscat/agent-dev-workflow') fail('plugin repository URL is wrong');
if (typeof plugin.skills !== 'string' || plugin.skills.trim() === '') fail('plugin skills path is missing');

const skillsPath = path.resolve(root, plugin.skills);
if (skillsPath !== path.join(root, 'skills')) {
  fail(`plugin skills path must resolve to the repository skills directory: ${plugin.skills}`);
}
if (!fs.existsSync(skillsPath) || !fs.statSync(skillsPath).isDirectory()) {
  fail(`plugin skills path does not resolve to a directory: ${plugin.skills}`);
}

for (const [field, value] of [
  ['interface.composerIcon', plugin.interface?.composerIcon],
  ['interface.logo', plugin.interface?.logo],
]) {
  if (typeof value !== 'string' || value.trim() === '') fail(`${field} is missing`);
  const resolved = path.resolve(root, value);
  const relative = path.relative(root, resolved);
  if (relative.startsWith(`..${path.sep}`) || relative === '..' || path.isAbsolute(relative)) {
    fail(`${field} must stay inside the repository: ${value}`);
  }
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
    fail(`${field} does not resolve to a file: ${value}`);
  }
}
NODE

echo "Checking documentation links..."
grep -q 'docs/workflow.md' README.md || fail "README must link workflow docs"
grep -q 'docs/multi-agent.md' README.md || fail "README must link multi-agent docs"
grep -q 'assets/logo.svg' README.md || fail "README must use the repository logo"
grep -q 'AGENTS.md' README.md || fail "README must link repository instructions"

echo "Checking whitespace..."
git diff --check
git diff --cached --check

if [[ -n "${VALIDATE_BASE_SHA:-}" || -n "${VALIDATE_HEAD_SHA:-}" ]]; then
  [[ -n "${VALIDATE_BASE_SHA:-}" && -n "${VALIDATE_HEAD_SHA:-}" ]] || \
    fail "VALIDATE_BASE_SHA and VALIDATE_HEAD_SHA must be set together"

  if [[ ! "$VALIDATE_BASE_SHA" =~ ^0+$ ]]; then
    git cat-file -e "$VALIDATE_BASE_SHA^{commit}" 2>/dev/null || fail "validation base commit is unavailable: $VALIDATE_BASE_SHA"
    git cat-file -e "$VALIDATE_HEAD_SHA^{commit}" 2>/dev/null || fail "validation head commit is unavailable: $VALIDATE_HEAD_SHA"
    git diff --check "$VALIDATE_BASE_SHA...$VALIDATE_HEAD_SHA"
  fi
fi

echo "Validation OK"
