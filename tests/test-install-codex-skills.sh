#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/agent-dev-workflow-install-tests.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

EXPECTED_SKILLS=(dev-auto dev-spec dev-plan dev-tdd dev-fix dev-verify dev-code-review dev-finish)
RETIRED_SKILLS=(dev-commit-writer dev-design-context dev-grill-docs dev-image-to-code swagger-doc-skill)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_file() { [[ -f "$1" ]] || fail "expected file: $1"; }
assert_dir() { [[ -d "$1" ]] || fail "expected directory: $1"; }
assert_not_exists() { [[ ! -e "$1" && ! -L "$1" ]] || fail "expected missing path: $1"; }
assert_contains() { grep -Fq -- "$2" "$1" || fail "expected '$2' in $1"; }

make_source() {
  local dir="$1"
  mkdir -p "$dir/scripts" "$dir/references" "$dir/skills"
  cp "$ROOT/scripts/install-codex-skills.sh" "$dir/scripts/"
  cp "$ROOT/scripts/validate-skill-package.sh" "$dir/scripts/"
  chmod +x "$dir/scripts/"*.sh
  printf '# baseline\n' > "$dir/references/dev-baseline.md"

  local skill
  for skill in "${EXPECTED_SKILLS[@]}"; do
    mkdir -p "$dir/skills/$skill/references"
    cat > "$dir/skills/$skill/SKILL.md" <<SKILL
---
name: $skill
description: "Fixture for $skill."
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
}

init_git_source() {
  local dir="$1"
  git -C "$dir" init -q -b master
  git -C "$dir" config user.name test
  git -C "$dir" config user.email test@example.invalid
  git -C "$dir" add .
  git -C "$dir" commit -qm initial
}

snapshot_tree() {
  local dir="$1" out="$2"
  (cd "$dir" && find . -mindepth 1 -print | LC_ALL=C sort | while IFS= read -r p; do
    if [[ -L "$p" ]]; then
      printf 'L\t%s\t%s\n' "$p" "$(readlink "$p")"
    elif [[ -d "$p" ]]; then
      printf 'D\t%s\n' "$p"
    elif [[ -f "$p" ]]; then
      printf 'F\t%s\t' "$p"
      if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$p" | awk '{print $1}'
      else
        shasum -a 256 "$p" | awk '{print $1}'
      fi
    fi
  done) > "$out"
}

run_expect_fail() {
  local log="$1"
  shift
  if "$@" >"$log" 2>&1; then
    cat "$log" >&2
    fail "command unexpectedly succeeded: $*"
  fi
}

echo "[install] clean install and manifest"
source1="$TMP/source-clean"
target1="$TMP/target-clean"
make_source "$source1"
init_git_source "$source1"
bash "$source1/scripts/install-codex-skills.sh" --target-dir "$target1" > "$TMP/clean.log"
for skill in "${EXPECTED_SKILLS[@]}"; do assert_file "$target1/$skill/SKILL.md"; done
assert_file "$target1/.agent-dev-workflow.manifest"
clean_head="$(git -C "$source1" rev-parse HEAD)"
assert_contains "$TMP/clean.log" "Installed revision: $clean_head"
assert_contains "$target1/.agent-dev-workflow.manifest" "$(printf 'source-dirty\t0')"

echo "[install] dirty skill source is reported explicitly"
source_dirty="$TMP/source-dirty"
target_dirty="$TMP/target-dirty"
make_source "$source_dirty"
init_git_source "$source_dirty"
dirty_head="$(git -C "$source_dirty" rev-parse HEAD)"
printf '\nlocal skill change\n' >> "$source_dirty/skills/dev-spec/SKILL.md"
bash "$source_dirty/scripts/install-codex-skills.sh" --target-dir "$target_dirty" > "$TMP/dirty.log"
assert_contains "$TMP/dirty.log" "Installed revision: $dirty_head (dirty)"
assert_contains "$target_dirty/.agent-dev-workflow.manifest" "$(printf 'source-dirty\t1')"

echo "[install] clean publication failures leave no partial target"
for step in $(seq 1 9); do
  target="$TMP/clean-fail-$step"
  if AGENT_DEV_WORKFLOW_TEST_FAIL_PUBLISH_AFTER="$step" \
      bash "$source1/scripts/install-codex-skills.sh" --target-dir "$target" >"$TMP/clean-fail-$step.log" 2>&1; then
    fail "clean injected failure step $step unexpectedly succeeded"
  fi
  assert_not_exists "$target"
done

echo "[install] unmanaged collision is preserved and refused"
source2="$TMP/source-unmanaged"
target2="$TMP/target-unmanaged"
make_source "$source2"
mkdir -p "$target2/dev-auto"
printf 'user data\n' > "$target2/dev-auto/user.txt"
run_expect_fail "$TMP/unmanaged.log" bash "$source2/scripts/install-codex-skills.sh" --target-dir "$target2"
assert_file "$target2/dev-auto/user.txt"
assert_contains "$TMP/unmanaged.log" "--migrate-legacy"

echo "[install] whole-source preflight fails before target changes"
source3="$TMP/source-preflight"
target3="$TMP/target-preflight"
make_source "$source3"
rm -rf "$source3/skills/dev-finish"
mkdir -p "$target3/dev-auto"
printf 'keep\n' > "$target3/dev-auto/keep.txt"
snapshot_tree "$target3" "$TMP/preflight.before"
run_expect_fail "$TMP/preflight.log" bash "$source3/scripts/install-codex-skills.sh" --target-dir "$target3" --migrate-legacy
snapshot_tree "$target3" "$TMP/preflight.after"
cmp -s "$TMP/preflight.before" "$TMP/preflight.after" || fail "preflight failure changed target"

echo "[install] every managed publication step rolls back"
source4="$TMP/source-rollback"
base_target="$TMP/target-base"
make_source "$source4"
init_git_source "$source4"
bash "$source4/scripts/install-codex-skills.sh" --target-dir "$base_target" >/dev/null
printf 'unrelated\n' > "$base_target/unrelated.txt"
# Change source content so a successful reinstall would be observable.
printf '\nnew revision\n' >> "$source4/skills/dev-spec/SKILL.md"
git -C "$source4" add . && git -C "$source4" commit -qm update

for step in $(seq 1 18); do
  target="$TMP/rollback-$step"
  cp -R "$base_target" "$target"
  snapshot_tree "$target" "$TMP/rollback-$step.before"
  if AGENT_DEV_WORKFLOW_TEST_FAIL_PUBLISH_AFTER="$step" \
      bash "$source4/scripts/install-codex-skills.sh" --target-dir "$target" >"$TMP/rollback-$step.log" 2>&1; then
    fail "injected failure step $step unexpectedly succeeded"
  fi
  snapshot_tree "$target" "$TMP/rollback-$step.after"
  cmp -s "$TMP/rollback-$step.before" "$TMP/rollback-$step.after" || {
    diff -u "$TMP/rollback-$step.before" "$TMP/rollback-$step.after" >&2 || true
    fail "rollback mismatch after publication step $step"
  }
done

echo "[install] trapped signals after every managed rename roll back completely"
for step in $(seq 1 18); do
  target="$TMP/signal-rollback-$step"
  cp -R "$base_target" "$target"
  snapshot_tree "$target" "$TMP/signal-rollback-$step.before"
  if AGENT_DEV_WORKFLOW_TEST_SIGNAL_AFTER_MV_STEP="$step" \
      bash "$source4/scripts/install-codex-skills.sh" --target-dir "$target" >"$TMP/signal-rollback-$step.log" 2>&1; then
    fail "signal injection after mutation step $step unexpectedly succeeded"
  fi
  snapshot_tree "$target" "$TMP/signal-rollback-$step.after"
  cmp -s "$TMP/signal-rollback-$step.before" "$TMP/signal-rollback-$step.after" || {
    diff -u "$TMP/signal-rollback-$step.before" "$TMP/signal-rollback-$step.after" >&2 || true
    fail "signal rollback mismatch after mutation step $step"
  }
done

echo "[install] local modifications in managed skills are preserved and refused"
target5="$TMP/target-modified"
cp -R "$base_target" "$target5"
printf 'local edit\n' >> "$target5/dev-plan/SKILL.md"
run_expect_fail "$TMP/modified.log" bash "$source4/scripts/install-codex-skills.sh" --target-dir "$target5"
assert_contains "$target5/dev-plan/SKILL.md" "local edit"
assert_contains "$TMP/modified.log" "modified locally"

echo "[install] 13-to-8 migration is explicit and preserves retired content"
source6="$TMP/source-legacy"
target6="$TMP/target-legacy"
make_source "$source6"
for skill in "${EXPECTED_SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
  mkdir -p "$target6/$skill"
  printf 'legacy %s\n' "$skill" > "$target6/$skill/legacy.txt"
done
printf 'unrelated\n' > "$target6/unrelated.txt"
run_expect_fail "$TMP/legacy-no-flag.log" bash "$source6/scripts/install-codex-skills.sh" --target-dir "$target6"
for skill in "${RETIRED_SKILLS[@]}"; do assert_file "$target6/$skill/legacy.txt"; done
bash "$source6/scripts/install-codex-skills.sh" --target-dir "$target6" --migrate-legacy > "$TMP/legacy.log"
for skill in "${EXPECTED_SKILLS[@]}"; do assert_file "$target6/$skill/SKILL.md"; done
for skill in "${RETIRED_SKILLS[@]}"; do assert_not_exists "$target6/$skill"; done
assert_file "$target6/unrelated.txt"
backup6="$(awk -F': ' '/Previous installation preserved at:/ {print $2}' "$TMP/legacy.log")"
assert_dir "$backup6"
for skill in "${RETIRED_SKILLS[@]}"; do assert_file "$backup6/$skill/legacy.txt"; done
assert_file "$backup6/dev-auto/legacy.txt"

echo "[install] every legacy-migration publication step rolls back"
for step in $(seq 1 22); do
  target="$TMP/legacy-rollback-$step"
  mkdir -p "$target"
  for skill in "${EXPECTED_SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
    mkdir -p "$target/$skill"
    printf 'legacy %s\n' "$skill" > "$target/$skill/legacy.txt"
  done
  printf 'unrelated\n' > "$target/unrelated.txt"
  snapshot_tree "$target" "$TMP/legacy-rollback-$step.before"
  if AGENT_DEV_WORKFLOW_TEST_FAIL_PUBLISH_AFTER="$step" \
      bash "$source6/scripts/install-codex-skills.sh" --target-dir "$target" --migrate-legacy >"$TMP/legacy-rollback-$step.log" 2>&1; then
    fail "legacy injected failure step $step unexpectedly succeeded"
  fi
  snapshot_tree "$target" "$TMP/legacy-rollback-$step.after"
  cmp -s "$TMP/legacy-rollback-$step.before" "$TMP/legacy-rollback-$step.after" || {
    diff -u "$TMP/legacy-rollback-$step.before" "$TMP/legacy-rollback-$step.after" >&2 || true
    fail "legacy rollback mismatch after publication step $step"
  }
done

echo "[install] nested and symlink-alias source targets fail before mutation"
source7="$TMP/source-overlap"
make_source "$source7"
init_git_source "$source7"
git_before="$(git -C "$source7" status --porcelain)"
run_expect_fail "$TMP/overlap.log" bash "$source7/scripts/install-codex-skills.sh" --target-dir "$source7/skills/dev-auto/nested"
[[ "$(git -C "$source7" status --porcelain)" == "$git_before" ]] || fail "nested overlap mutated source"
ln -s "$source7/skills" "$TMP/skills-link"
run_expect_fail "$TMP/overlap-symlink.log" bash "$source7/scripts/install-codex-skills.sh" --target-dir "$TMP/skills-link/dev-auto/nested"
[[ "$(git -C "$source7" status --porcelain)" == "$git_before" ]] || fail "symlink overlap mutated source"

echo "[install] symlink plus parent components resolve with filesystem semantics"
physical_root="$TMP/path-physical/codex"
mkdir -p "$physical_root/config"
path_link="$TMP/path-link"
ln -s "$physical_root/config" "$path_link"
requested_target="$path_link/../skills"
lexically_collapsed_target="$TMP/skills"
bash "$source1/scripts/install-codex-skills.sh" --target-dir "$requested_target" > "$TMP/path-resolution.log"
assert_file "$physical_root/skills/dev-auto/SKILL.md"
assert_not_exists "$lexically_collapsed_target"
assert_contains "$TMP/path-resolution.log" "Installed 8 Agent Dev Workflow skills to $physical_root/skills"

echo "[install] active lock refuses concurrent installer"
source8="$TMP/source-lock"
target8="$TMP/target-lock"
make_source "$source8"
mkdir -p "${target8}.agent-dev-workflow.lock"
run_expect_fail "$TMP/lock.log" bash "$source8/scripts/install-codex-skills.sh" --target-dir "$target8"
assert_not_exists "$target8"

echo "[install] linked worktree --upgrade follows upstream and installs updated content"
seed="$TMP/upgrade-seed"
origin="$TMP/origin.git"
worktree="$TMP/upgrade-worktree"
target9="$TMP/target-upgrade"
make_source "$seed"
init_git_source "$seed"
git clone -q --bare "$seed" "$origin"
git -C "$seed" remote add origin "$origin"
git -C "$seed" push -qu origin master
git -C "$seed" worktree add -qb linked "$worktree" master
git -C "$worktree" branch --set-upstream-to=origin/master linked >/dev/null
printf '\nupstream marker\n' >> "$seed/skills/dev-auto/SKILL.md"
git -C "$seed" add . && git -C "$seed" commit -qm upstream-update
git -C "$seed" push -q origin master
expected_head="$(git -C "$seed" rev-parse HEAD)"
bash "$worktree/scripts/install-codex-skills.sh" --upgrade --target-dir "$target9" > "$TMP/upgrade.log"
[[ "$(git -C "$worktree" rev-parse HEAD)" == "$expected_head" ]] || fail "linked worktree did not fast-forward"
assert_contains "$target9/dev-auto/SKILL.md" "upstream marker"
assert_contains "$TMP/upgrade.log" "Installed revision: $expected_head"

echo "[install] detached --upgrade fails instead of reporting stale success"
detached="$TMP/detached"
git clone -q "$origin" "$detached"
git -C "$detached" checkout -q --detach HEAD
run_expect_fail "$TMP/detached.log" bash "$detached/scripts/install-codex-skills.sh" --upgrade --target-dir "$TMP/detached-target"
assert_contains "$TMP/detached.log" "attached branch"

printf 'Installer regression tests passed\n'
