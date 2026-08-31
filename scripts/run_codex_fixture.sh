#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="${PROJECT_DIR}/fixtures/agent"
WORK_DIR="$(mktemp -d -t rapid-mlx-agent.XXXXXX)"
cp -R "${FIXTURE_DIR}/." "${WORK_DIR}/"

echo "Disposable fixture: ${WORK_DIR}"
echo "The directory is retained after Codex exits for inspection."
codex --profile rapid-mlx -C "${WORK_DIR}" \
  "Run the tests, fix the subtraction bug, add an edge-case test, and summarize the changes."

