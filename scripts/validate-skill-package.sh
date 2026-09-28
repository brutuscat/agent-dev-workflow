#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
BASELINE_FILE="$ROOT/references/dev-baseline.md"

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

usage() {
  cat <<'USAGE'
Usage: bash scripts/validate-skill-package.sh [--skills-dir DIR] [--baseline FILE]

Validate the installable Agent Dev Workflow skill package.
USAGE
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skills-dir)
      [[ $# -ge 2 ]] || fail "--skills-dir requires a directory"
      SKILLS_DIR="$2"
      shift 2
      ;;
    --baseline)
      [[ $# -ge 2 ]] || fail "--baseline requires a file"
      BASELINE_FILE="$2"
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

[[ -d "$SKILLS_DIR" ]] || fail "skills directory not found: $SKILLS_DIR"
[[ -f "$BASELINE_FILE" ]] || fail "baseline not found: $BASELINE_FILE"

actual_skills="$(
  for dir in "$SKILLS_DIR"/*; do
    [[ -d "$dir" ]] && basename "$dir"
  done | LC_ALL=C sort
)"
expected_skills="$(printf '%s\n' "${EXPECTED_SKILLS[@]}" | LC_ALL=C sort)"

[[ "$actual_skills" == "$expected_skills" ]] || {
  echo "Expected skills:" >&2
  echo "$expected_skills" >&2
  echo "Actual skills:" >&2
  echo "$actual_skills" >&2
  fail "skill set does not match"
}

scalar_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  local normalized

  case "$value" in
    \"*)
      [[ "$value" == *\" ]] || fail "$file has malformed quoted $key frontmatter"
      normalized="${value:1:${#value}-2}"
      ;;
    \'*)
      [[ "$value" == *\' ]] || fail "$file has malformed quoted $key frontmatter"
      normalized="${value:1:${#value}-2}"
      ;;
    \[*|\{*|\|*|\>*|'&'*|'*'*|'!'*)
      fail "$file requires $key to be a scalar string"
      ;;
    *)
      if [[ "$value" == \#* ]]; then
        normalized=""
      else
        normalized="${value%%[[:space:]]#*}"
      fi
      while [[ "$normalized" == *[[:space:]] ]]; do
        normalized="${normalized%?}"
      done
      case "$normalized" in
        ''|'~'|null|Null|NULL|true|True|TRUE|false|False|FALSE)
          fail "$file requires $key to be a nonempty string"
          ;;
      esac
      [[ ! "$normalized" =~ ^[-+]?[0-9]+([.][0-9]+)?$ ]] || \
        fail "$file requires $key to be a string, not a number"
      ;;
  esac

  printf '%s\n' "$normalized"
}

validate_scalar_syntax() {
  local file="$1"
  local key="$2"
  local value="$3"

  case "$value" in
    \"*)
      [[ "$value" == *\" ]] || fail "$file has malformed quoted $key frontmatter"
      ;;
    \'*)
      [[ "$value" == *\' ]] || fail "$file has malformed quoted $key frontmatter"
      ;;
    \[*|\{*)
      case "$value" in
        \[*\]|\{*\}) ;;
        *) fail "$file has malformed $key frontmatter" ;;
      esac
      ;;
    \|*|\>*)
      fail "$file uses unsupported multiline $key frontmatter"
      ;;
    '&'*|'*'*|'!'*)
      fail "$file uses unsupported anchored/tagged $key frontmatter"
      ;;
  esac
}

parse_frontmatter() {
  local file="$1"
  local line key value line_number=0 closed=0
  local seen='|'

  while IFS= read -r line || [[ -n "$line" ]]; do
    line_number=$((line_number + 1))

    if [[ "$line_number" -eq 1 ]]; then
      [[ "$line" == "---" ]] || fail "$file must start with YAML frontmatter"
      continue
    fi

    if [[ "$line" == "---" ]]; then
      closed=1
      break
    fi

    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" != [[:space:]]* ]] || fail "$file uses unsupported nested frontmatter at line $line_number"
    [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_-]*):[[:space:]]*(.*)$ ]] || \
      fail "$file has malformed frontmatter at line $line_number"

    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    [[ "$seen" != *"|$key|"* ]] || fail "$file has duplicate $key frontmatter"
    seen+="$key|"
    validate_scalar_syntax "$file" "$key" "$value"
  done < "$file"

  [[ "$closed" -eq 1 ]] || fail "$file is missing the closing frontmatter delimiter"
}

frontmatter_field() {
  local file="$1"
  local key="$2"

  awk -v key="$key" '
    NR == 1 { in_frontmatter = ($0 == "---"); next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter {
      prefix = key ":"
      if (index($0, prefix) == 1) {
        value = substr($0, length(prefix) + 1)
        sub(/^[[:space:]]+/, "", value)
        print value
        found = 1
        exit
      }
    }
    END { exit(found ? 0 : 1) }
  ' "$file"
}

validate_frontmatter() {
  local skill="$1"
  local file="$2"
  local name_raw description_raw name description

  parse_frontmatter "$file"

  if ! name_raw="$(frontmatter_field "$file" name)"; then
    fail "$file is missing name frontmatter"
  fi
  if ! description_raw="$(frontmatter_field "$file" description)"; then
    fail "$file is missing description frontmatter"
  fi

  name="$(scalar_value "$file" name "$name_raw")"
  description="$(scalar_value "$file" description "$description_raw")"

  [[ -n "$name" ]] || fail "$file has an empty name"
  [[ -n "$description" ]] || fail "$file has an empty description"
  [[ "$name" == "$skill" ]] || fail "$file frontmatter name '$name' does not match directory '$skill'"
}

validate_references() {
  local skill_dir="$1"
  local file="$skill_dir/SKILL.md"
  local ref

  while IFS= read -r ref; do
    [[ -n "$ref" ]] || continue
    [[ -f "$skill_dir/$ref" ]] || fail "$file references missing resource: $ref"
  done < <(grep -Eo 'references/[A-Za-z0-9._/-]+\.md' "$file" | LC_ALL=C sort -u || true)
}

for skill in "${EXPECTED_SKILLS[@]}"; do
  skill_dir="$SKILLS_DIR/$skill"
  file="$skill_dir/SKILL.md"
  [[ -f "$file" ]] || fail "$file missing"
  validate_frontmatter "$skill" "$file"

  [[ -f "$skill_dir/references/dev-baseline.md" ]] || fail "$skill baseline copy missing"
  cmp -s "$BASELINE_FILE" "$skill_dir/references/dev-baseline.md" || fail "$skill baseline copy drifted"

  validate_references "$skill_dir"
done

AUTO_POLICY="$SKILLS_DIR/dev-auto/agents/openai.yaml"
[[ -f "$AUTO_POLICY" ]] || fail "dev-auto explicit invocation policy missing: $AUTO_POLICY"
awk '
  /^[[:space:]]*policy:[[:space:]]*$/ { in_policy = 1; next }
  in_policy && /^[^[:space:]]/ { in_policy = 0 }
  in_policy && /^[[:space:]]+allow_implicit_invocation:[[:space:]]*false[[:space:]]*$/ { found = 1 }
  END { exit(found ? 0 : 1) }
' "$AUTO_POLICY" || fail "dev-auto must keep policy.allow_implicit_invocation: false"

echo "Skill package OK: ${#EXPECTED_SKILLS[@]} skills"
