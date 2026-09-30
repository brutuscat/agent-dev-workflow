#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT/skills"
TARGET_DIR="${CODEX_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"
MODE="install"
MIGRATE_LEGACY=0

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

RETIRED_SKILLS=(
  dev-commit-writer
  dev-design-context
  dev-grill-docs
  dev-image-to-code
  swagger-doc-skill
)

usage() {
  cat <<'USAGE'
Usage: bash scripts/install-codex-skills.sh [--upgrade] [--migrate-legacy] [--target-dir DIR]

Safely install Agent Dev Workflow skills into Codex's skills directory.

Options:
  --upgrade         Fast-forward this Git checkout, then run the updated installer.
  --migrate-legacy  Back up and retire pre-manifest Agent Dev Workflow directories.
                    Use this once when migrating an older 13-skill installation.
  --target-dir DIR  Install into DIR instead of ${CODEX_HOME:-$HOME/.codex}/skills.
  -h, --help        Show this help.
USAGE
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upgrade)
      MODE="upgrade"
      shift
      ;;
    --migrate-legacy)
      MIGRATE_LEGACY=1
      shift
      ;;
    --target-dir)
      [[ $# -ge 2 ]] || fail "--target-dir requires a directory"
      TARGET_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

absolute_path_preserving_components() {
  local input="$1"

  if [[ "$input" == /* ]]; then
    printf '%s\n' "$input"
  else
    printf '%s/%s\n' "$(pwd -P)" "$input"
  fi
}

canonical_path() {
  local probe parent base component
  local -a suffix

  probe="$(absolute_path_preserving_components "$1")"
  suffix=()

  # Walk upward without collapsing "." or "..". The kernel resolves existing
  # components first, so symlinks retain normal filesystem path semantics.
  while [[ ! -e "$probe" && ! -L "$probe" ]]; do
    [[ "$probe" != "/" ]] || break
    base="$(basename "$probe")"
    suffix=("$base" "${suffix[@]}")
    parent="$(dirname "$probe")"
    [[ "$parent" != "$probe" ]] || break
    probe="$parent"
  done

  if [[ -d "$probe" ]]; then
    probe="$(cd "$probe" && pwd -P)"
  elif [[ -e "$probe" || -L "$probe" ]]; then
    if [[ ${#suffix[@]} -gt 0 ]]; then
      fail "target path traverses a non-directory component: $probe"
    fi
    parent="$(cd "$(dirname "$probe")" && pwd -P)"
    probe="$parent/$(basename "$probe")"
  else
    fail "could not resolve target path: $1"
  fi

  # The remaining suffix did not exist when inspected, so no remaining
  # component can be a symlink. Collapse only that unresolved suffix.
  for component in "${suffix[@]}"; do
    case "$component" in
      ''|'.') ;;
      '..')
        [[ "$probe" == "/" ]] || probe="$(dirname "$probe")"
        ;;
      *)
        if [[ "$probe" == "/" ]]; then
          probe="/$component"
        else
          probe="$probe/$component"
        fi
        ;;
    esac
  done

  printf '%s\n' "$probe"
}

paths_overlap() {
  local a="$1"
  local b="$2"
  [[ "$a" == "$b" || "$a" == "$b"/* || "$b" == "$a"/* ]]
}

sha256_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    fail "sha256sum or shasum is required"
  fi
}

directory_digest() {
  local dir="$1"
  local listing rel digest
  listing="$(mktemp "${TMPDIR:-/tmp}/agent-dev-workflow-digest.XXXXXX")"

  while IFS= read -r rel; do
    [[ -n "$rel" ]] || continue
    if [[ -L "$dir/$rel" ]]; then
      printf 'L\t%s\t%s\n' "$(readlink "$dir/$rel")" "$rel" >> "$listing"
    elif [[ -d "$dir/$rel" ]]; then
      printf 'D\t%s\n' "$rel" >> "$listing"
    elif [[ -f "$dir/$rel" ]]; then
      digest="$(sha256_file "$dir/$rel")"
      printf 'F\t%s\t%s\n' "$digest" "$rel" >> "$listing"
    else
      fail "unsupported filesystem entry in skill package: $dir/$rel"
    fi
  done < <(cd "$dir" && find . -mindepth 1 \
    \( -type f -o -type d -o -type l \) -print | LC_ALL=C sort)

  digest="$(sha256_file "$listing")"
  rm -f "$listing"
  printf '%s\n' "$digest"
}

manifest_digest() {
  local manifest="$1"
  local skill="$2"
  awk -F '\t' -v skill="$skill" '$1 == "skill" && $2 == skill { print $3; found = 1 } END { exit(found ? 0 : 1) }' "$manifest"
}

validate_manifest() {
  local manifest="$1"
  local skill digest

  grep -qx $'format\t1' "$manifest" || fail "unsupported or corrupt package manifest: $manifest"
  grep -qx $'package\tagent-dev-workflow' "$manifest" || fail "package manifest belongs to another package: $manifest"

  for skill in "${EXPECTED_SKILLS[@]}"; do
    if ! digest="$(manifest_digest "$manifest" "$skill")"; then
      fail "package manifest is missing $skill: $manifest"
    fi
    [[ "$digest" =~ ^[0-9a-fA-F]{64}$ ]] || fail "package manifest has invalid digest for $skill"
  done
}

[[ -d "$SOURCE_DIR" ]] || fail "skills directory not found: $SOURCE_DIR"
[[ -n "$TARGET_DIR" ]] || fail "target directory must not be empty"

SOURCE_REALPATH="$(canonical_path "$SOURCE_DIR")"
TARGET_REALPATH="$(canonical_path "$TARGET_DIR")"
[[ "$TARGET_REALPATH" != "/" ]] || fail "unsafe target directory: $TARGET_DIR"
paths_overlap "$SOURCE_REALPATH" "$TARGET_REALPATH" && \
  fail "target directory must not overlap repository skills: $TARGET_REALPATH"

if [[ "$MODE" == "upgrade" ]]; then
  [[ "$(git -C "$ROOT" rev-parse --is-inside-work-tree 2>/dev/null || true)" == "true" ]] || \
    fail "--upgrade requires a Git worktree"
  git -C "$ROOT" symbolic-ref --quiet --short HEAD >/dev/null || \
    fail "--upgrade requires an attached branch"
  git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1 || \
    fail "--upgrade requires the current branch to have an upstream"

  git -C "$ROOT" pull --ff-only

  args=(--target-dir "$TARGET_REALPATH")
  [[ "$MIGRATE_LEGACY" -eq 1 ]] && args+=(--migrate-legacy)
  exec bash "$ROOT/scripts/install-codex-skills.sh" "${args[@]}"
fi

bash "$ROOT/scripts/validate-skill-package.sh" \
  --skills-dir "$SOURCE_DIR" \
  --baseline "$ROOT/references/dev-baseline.md"

PARENT_DIR="$(dirname "$TARGET_REALPATH")"
mkdir -p "$PARENT_DIR"

LOCK_DIR="${TARGET_REALPATH}.agent-dev-workflow.lock"
LOCK_OWNED=0
STAGE_DIR=""
BACKUP_DIR=""
ROLLBACK_NEEDED=0
TARGET_CREATED=0
PUBLISH_STEP=0
MUTATION_STEP=0
MUTATION_ACTIVE=0
DEFERRED_SIGNAL_STATUS=0
PUBLISHED_PATHS=()
BACKED_UP_NAMES=()

rollback() {
  local i path name

  for ((i = ${#PUBLISHED_PATHS[@]} - 1; i >= 0; i--)); do
    path="${PUBLISHED_PATHS[$i]}"
    rm -rf "$path"
  done

  if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
    for ((i = ${#BACKED_UP_NAMES[@]} - 1; i >= 0; i--)); do
      name="${BACKED_UP_NAMES[$i]}"
      if [[ -e "$BACKUP_DIR/$name" || -L "$BACKUP_DIR/$name" ]]; then
        mv "$BACKUP_DIR/$name" "$TARGET_REALPATH/$name"
      fi
    done
    rmdir "$BACKUP_DIR" 2>/dev/null || true
  fi

  if [[ "$TARGET_CREATED" -eq 1 ]]; then
    rmdir "$TARGET_REALPATH" 2>/dev/null || true
  fi
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM

  if [[ "$status" -ne 0 && "$ROLLBACK_NEEDED" -eq 1 ]]; then
    echo "Install failed; restoring previous installation." >&2
    rollback || echo "ERROR: rollback was incomplete; inspect $BACKUP_DIR" >&2
  fi

  [[ -z "$STAGE_DIR" || ! -d "$STAGE_DIR" ]] || rm -rf "$STAGE_DIR"
  [[ "$LOCK_OWNED" -eq 0 ]] || rm -rf "$LOCK_DIR"
  exit "$status"
}

handle_signal() {
  local status="$1"

  if [[ "$MUTATION_ACTIVE" -eq 1 ]]; then
    DEFERRED_SIGNAL_STATUS="$status"
    return 0
  fi

  exit "$status"
}

trap cleanup EXIT
trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  fail "another installer may be using this target: $LOCK_DIR"
fi
LOCK_OWNED=1
printf '%s\n' "$$" > "$LOCK_DIR/pid"

STAGE_DIR="$(mktemp -d "${TARGET_REALPATH}.agent-dev-workflow-stage.XXXXXX")"
for skill in "${EXPECTED_SKILLS[@]}"; do
  cp -R "$SOURCE_DIR/$skill" "$STAGE_DIR/$skill"
done

bash "$ROOT/scripts/validate-skill-package.sh" \
  --skills-dir "$STAGE_DIR" \
  --baseline "$ROOT/references/dev-baseline.md"

MANIFEST_PATH="$TARGET_REALPATH/.agent-dev-workflow.manifest"
MANIFEST_STAGE="$STAGE_DIR/.agent-dev-workflow.manifest"
REVISION="unversioned"
SOURCE_DIRTY=0
if [[ "$(git -C "$ROOT" rev-parse --is-inside-work-tree 2>/dev/null || true)" == "true" ]]; then
  REVISION="$(git -C "$ROOT" rev-parse HEAD)"
  if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=all -- skills)" ]]; then
    SOURCE_DIRTY=1
  fi
fi

{
  printf 'format\t1\n'
  printf 'package\tagent-dev-workflow\n'
  printf 'revision\t%s\n' "$REVISION"
  printf 'source-dirty\t%s\n' "$SOURCE_DIRTY"
  for skill in "${EXPECTED_SKILLS[@]}"; do
    printf 'skill\t%s\t%s\n' "$skill" "$(directory_digest "$STAGE_DIR/$skill")"
  done
} > "$MANIFEST_STAGE"

HAS_MANIFEST=0
if [[ -e "$MANIFEST_PATH" || -L "$MANIFEST_PATH" ]]; then
  [[ -f "$MANIFEST_PATH" ]] || fail "package manifest path is not a regular file: $MANIFEST_PATH"
  validate_manifest "$MANIFEST_PATH"
  HAS_MANIFEST=1
fi

legacy_collision=0
for retired in "${RETIRED_SKILLS[@]}"; do
  if [[ -e "$TARGET_REALPATH/$retired" || -L "$TARGET_REALPATH/$retired" ]]; then
    legacy_collision=1
  fi
done

if [[ "$HAS_MANIFEST" -eq 1 ]]; then
  for skill in "${EXPECTED_SKILLS[@]}"; do
    if [[ -e "$TARGET_REALPATH/$skill" || -L "$TARGET_REALPATH/$skill" ]]; then
      [[ -d "$TARGET_REALPATH/$skill" ]] || fail "managed skill path is not a directory: $TARGET_REALPATH/$skill"
      installed_digest="$(directory_digest "$TARGET_REALPATH/$skill")"
      recorded_digest="$(manifest_digest "$MANIFEST_PATH" "$skill")"
      [[ "$installed_digest" == "$recorded_digest" ]] || \
        fail "managed skill was modified locally: $skill; preserve or move those changes before reinstalling"
    fi
  done

  if [[ "$legacy_collision" -eq 1 && "$MIGRATE_LEGACY" -ne 1 ]]; then
    fail "retired legacy skills still exist; inspect them and rerun with --migrate-legacy only if you want them backed up and retired"
  fi
else
  unmanaged_collision=0
  for skill in "${EXPECTED_SKILLS[@]}"; do
    if [[ -e "$TARGET_REALPATH/$skill" || -L "$TARGET_REALPATH/$skill" ]]; then
      if [[ ! -d "$TARGET_REALPATH/$skill" ]]; then
        unmanaged_collision=1
        continue
      fi
      installed_digest="$(directory_digest "$TARGET_REALPATH/$skill")"
      staged_digest="$(directory_digest "$STAGE_DIR/$skill")"
      [[ "$installed_digest" == "$staged_digest" ]] || unmanaged_collision=1
    fi
  done

  if [[ "$unmanaged_collision" -eq 1 || "$legacy_collision" -eq 1 ]]; then
    [[ "$MIGRATE_LEGACY" -eq 1 ]] || \
      fail "pre-manifest or unmanaged skill directories exist; rerun with --migrate-legacy to back them up before takeover"
  fi
fi

if [[ ! -d "$TARGET_REALPATH" ]]; then
  mkdir "$TARGET_REALPATH"
  TARGET_CREATED=1
fi

BACKUP_NEEDED=0
for skill in "${EXPECTED_SKILLS[@]}"; do
  [[ ! -e "$TARGET_REALPATH/$skill" && ! -L "$TARGET_REALPATH/$skill" ]] || BACKUP_NEEDED=1
done
[[ ! -e "$MANIFEST_PATH" && ! -L "$MANIFEST_PATH" ]] || BACKUP_NEEDED=1
if [[ "$MIGRATE_LEGACY" -eq 1 ]]; then
  [[ "$legacy_collision" -eq 0 ]] || BACKUP_NEEDED=1
fi

if [[ "$BACKUP_NEEDED" -eq 1 ]]; then
  BACKUP_DIR="$(mktemp -d "${TARGET_REALPATH}.agent-dev-workflow-backup.XXXXXX")"
fi

maybe_inject_failure() {
  PUBLISH_STEP=$((PUBLISH_STEP + 1))
  if [[ -n "${AGENT_DEV_WORKFLOW_TEST_FAIL_PUBLISH_AFTER:-}" && \
        "$PUBLISH_STEP" -eq "${AGENT_DEV_WORKFLOW_TEST_FAIL_PUBLISH_AFTER}" ]]; then
    echo "ERROR: injected publication failure after step $PUBLISH_STEP" >&2
    return 97
  fi
}

begin_mutation() {
  MUTATION_STEP=$((MUTATION_STEP + 1))
  MUTATION_ACTIVE=1
}

maybe_inject_signal_after_mv() {
  if [[ -n "${AGENT_DEV_WORKFLOW_TEST_SIGNAL_AFTER_MV_STEP:-}" && \
        "$MUTATION_STEP" == "${AGENT_DEV_WORKFLOW_TEST_SIGNAL_AFTER_MV_STEP}" ]]; then
    kill -TERM "$"
  fi
}

end_mutation() {
  local status

  MUTATION_ACTIVE=0
  if [[ "$DEFERRED_SIGNAL_STATUS" -ne 0 ]]; then
    status="$DEFERRED_SIGNAL_STATUS"
    DEFERRED_SIGNAL_STATUS=0
    exit "$status"
  fi
}

backup_existing() {
  local name="$1"
  [[ -e "$TARGET_REALPATH/$name" || -L "$TARGET_REALPATH/$name" ]] || return 0

  begin_mutation
  mv "$TARGET_REALPATH/$name" "$BACKUP_DIR/$name"
  maybe_inject_signal_after_mv
  BACKED_UP_NAMES+=("$name")
  end_mutation

  maybe_inject_failure
}

publish_staged() {
  local source="$1"
  local destination="$2"

  begin_mutation
  mv "$source" "$destination"
  maybe_inject_signal_after_mv
  PUBLISHED_PATHS+=("$destination")
  end_mutation

  maybe_inject_failure
}

ROLLBACK_NEEDED=1

for skill in "${EXPECTED_SKILLS[@]}"; do
  backup_existing "$skill"
done
backup_existing ".agent-dev-workflow.manifest"

if [[ "$MIGRATE_LEGACY" -eq 1 ]]; then
  for retired in "${RETIRED_SKILLS[@]}"; do
    backup_existing "$retired"
  done
fi

for skill in "${EXPECTED_SKILLS[@]}"; do
  publish_staged "$STAGE_DIR/$skill" "$TARGET_REALPATH/$skill"
done
publish_staged "$MANIFEST_STAGE" "$MANIFEST_PATH"

ROLLBACK_NEEDED=0

printf 'Installed %d Agent Dev Workflow skills to %s\n' "${#EXPECTED_SKILLS[@]}" "$TARGET_REALPATH"
if [[ "$SOURCE_DIRTY" -eq 1 ]]; then
  printf 'Installed revision: %s (dirty)\n' "$REVISION"
else
  printf 'Installed revision: %s\n' "$REVISION"
fi
if [[ -n "$BACKUP_DIR" ]]; then
  printf 'Previous installation preserved at: %s\n' "$BACKUP_DIR"
fi
