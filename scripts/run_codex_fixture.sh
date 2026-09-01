#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="${PROJECT_DIR}/fixtures/agent"
WORK_DIR="$(mktemp -d -t rapid-mlx-agent.XXXXXX)"
BASE_URL="${RAPID_MLX_BASE_URL:-http://127.0.0.1:8000/v1}"
cp -R "${FIXTURE_DIR}/." "${WORK_DIR}/"
ln -s "${PROJECT_DIR}/.venv/bin/pytest" "${WORK_DIR}/test-runner"
git -C "${WORK_DIR}" init -q
git -C "${WORK_DIR}" config user.name "Rapid-MLX Fixture"
git -C "${WORK_DIR}" config user.email "fixture@localhost"
git -C "${WORK_DIR}" add .
git -C "${WORK_DIR}" commit -qm "fixture baseline"

echo "Disposable fixture: ${WORK_DIR}"
echo "The directory is retained after Codex exits for inspection."
PATH="${PROJECT_DIR}/.venv/bin:${PATH}" codex --strict-config --profile rapid-mlx \
  -c "model_providers.rapid-mlx.base_url=\"${BASE_URL}\"" \
  --sandbox workspace-write --ask-for-approval never exec -C "${WORK_DIR}" \
  "Work only in the current disposable directory and do not inspect parent directories. Use ./test-runner for tests; do not install packages or create an environment. Run the tests, fix the subtraction bug, add an edge-case test, then rename subtract to difference across the implementation and tests. Use the apply_patch tool for file edits. Rerun the tests and summarize the changes."

"${PROJECT_DIR}/.venv/bin/python" -m pytest -q "${WORK_DIR}"
(
  cd "${WORK_DIR}"
  "${PROJECT_DIR}/.venv/bin/python" -c \
    'import calculator; assert hasattr(calculator, "difference"); assert not hasattr(calculator, "subtract")'
)
git -C "${WORK_DIR}" diff --check
