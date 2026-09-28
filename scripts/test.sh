#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$ROOT/tests/test-install-codex-skills.sh"
bash "$ROOT/tests/test-validate-repo.sh"
