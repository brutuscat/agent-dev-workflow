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

validate_frontmatter_package() {
  command -v ruby >/dev/null 2>&1 || fail "ruby is required to validate SKILL.md YAML frontmatter"

  ruby - "$SKILLS_DIR" "${EXPECTED_SKILLS[@]}" <<'RUBY'
require "yaml"

skills_dir = ARGV.shift
expected_skills = ARGV

def fail!(message)
  warn "ERROR: #{message}"
  exit 1
end

def safe_load_yaml(text)
  parameters = YAML.method(:safe_load).parameters
  keyword_aliases = parameters.any? do |kind, name|
    [:key, :keyreq].include?(kind) && name == :aliases
  end

  if keyword_aliases
    YAML.safe_load(text, aliases: false)
  else
    YAML.safe_load(text, [], [], false)
  end
end

def validate_skill!(skills_dir, skill)
  file = File.join(skills_dir, skill, "SKILL.md")
  fail!("#{file} missing") unless File.file?(file)

  content = File.read(file, encoding: "UTF-8")
  fail!("#{file} is not valid UTF-8") unless content.valid_encoding?

  lines = content.lines
  fail!("#{file} must start with YAML frontmatter") unless lines.first&.chomp == "---"

  closing = (1...lines.length).find { |index| lines[index].chomp == "---" }
  fail!("#{file} is missing the closing frontmatter delimiter") unless closing

  frontmatter = lines[1...closing].join

  begin
    metadata = safe_load_yaml(frontmatter)
  rescue Psych::Exception => error
    detail = error.message.lines.first.to_s.strip
    fail!("#{file} has invalid YAML frontmatter: #{detail}")
  end

  fail!("#{file} frontmatter must be a YAML mapping") unless metadata.is_a?(Hash)

  allowed_fields = %w[name description license compatibility metadata allowed-tools]
  unknown_fields = metadata.keys.reject { |key| key.is_a?(String) && allowed_fields.include?(key) }
  unless unknown_fields.empty?
    fail!("#{file} has unsupported frontmatter fields: #{unknown_fields.map(&:inspect).join(", ")}")
  end

  name = metadata["name"]
  unless name.is_a?(String) && !name.strip.empty?
    fail!("#{file} field 'name' must be a non-empty string")
  end

  normalized_name = name.strip.unicode_normalize(:nfkc)
  fail!("#{file} name exceeds 64 characters") if normalized_name.length > 64
  fail!("#{file} name must be lowercase") unless normalized_name == normalized_name.downcase
  fail!("#{file} name cannot start or end with a hyphen") if normalized_name.start_with?("-") || normalized_name.end_with?("-")
  fail!("#{file} name cannot contain consecutive hyphens") if normalized_name.include?("--")
  unless normalized_name.match?(/\A[\p{Alnum}-]+\z/u)
    fail!("#{file} name may contain only letters, digits, and hyphens")
  end

  directory_name = File.basename(File.dirname(file)).unicode_normalize(:nfkc)
  fail!("#{file} name '#{normalized_name}' does not match directory '#{directory_name}'") unless normalized_name == directory_name
  fail!("#{file} name '#{normalized_name}' does not match expected skill '#{skill}'") unless normalized_name == skill

  description = metadata["description"]
  unless description.is_a?(String) && !description.strip.empty?
    fail!("#{file} field 'description' must be a non-empty string")
  end
  fail!("#{file} description exceeds 1024 characters") if description.length > 1024

  if metadata.key?("compatibility")
    compatibility = metadata["compatibility"]
    unless compatibility.is_a?(String) && !compatibility.empty?
      fail!("#{file} field 'compatibility' must be a non-empty string")
    end
    fail!("#{file} compatibility exceeds 500 characters") if compatibility.length > 500
  end

  %w[license allowed-tools].each do |field|
    next unless metadata.key?(field)
    fail!("#{file} field '#{field}' must be a string") unless metadata[field].is_a?(String)
  end

  if metadata.key?("metadata")
    nested = metadata["metadata"]
    fail!("#{file} field 'metadata' must be a string-to-string mapping") unless nested.is_a?(Hash)
    unless nested.all? { |key, value| key.is_a?(String) && value.is_a?(String) }
      fail!("#{file} field 'metadata' must contain only string keys and string values")
    end
  end
end

expected_skills.each { |skill| validate_skill!(skills_dir, skill) }
RUBY
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

validate_frontmatter_package

for skill in "${EXPECTED_SKILLS[@]}"; do
  skill_dir="$SKILLS_DIR/$skill"
  file="$skill_dir/SKILL.md"
  [[ -f "$file" ]] || fail "$file missing"

  [[ -f "$skill_dir/references/dev-baseline.md" ]] || fail "$skill baseline copy missing"
  cmp -s "$BASELINE_FILE" "$skill_dir/references/dev-baseline.md" || fail "$skill baseline copy drifted"

  validate_references "$skill_dir"
done

AUTO_POLICY="$SKILLS_DIR/dev-auto/agents/openai.yaml"
[[ -f "$AUTO_POLICY" ]] || fail "dev-auto explicit invocation policy missing: $AUTO_POLICY"

ruby - "$AUTO_POLICY" <<'RUBY'
require "yaml"

file = ARGV.fetch(0)

def fail!(message)
  warn "ERROR: #{message}"
  exit 1
end

def safe_load_yaml(text)
  parameters = YAML.method(:safe_load).parameters
  keyword_aliases = parameters.any? do |kind, name|
    [:key, :keyreq].include?(kind) && name == :aliases
  end

  if keyword_aliases
    YAML.safe_load(text, aliases: false)
  else
    YAML.safe_load(text, [], [], false)
  end
end

begin
  document = safe_load_yaml(File.read(file, encoding: "UTF-8"))
rescue Psych::Exception => error
  detail = error.message.lines.first.to_s.strip
  fail!("#{file} has invalid YAML: #{detail}")
end

fail!("#{file} must be a YAML mapping") unless document.is_a?(Hash)

policy = document["policy"]
fail!("#{file} must define a top-level policy mapping") unless policy.is_a?(Hash)

value = policy["allow_implicit_invocation"]
unless value.equal?(false)
  fail!("#{file} must keep top-level policy.allow_implicit_invocation as boolean false")
end
RUBY

echo "Skill package OK: ${#EXPECTED_SKILLS[@]} skills"
