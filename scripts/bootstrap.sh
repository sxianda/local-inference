#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
VENV_DIR="${PROJECT_DIR}/.venv"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "error: ${PYTHON_BIN} is required" >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -e "${PROJECT_DIR}[dev,model-download]"

if [[ -f "${PROJECT_DIR}/vendor/Rapid-MLX/pyproject.toml" ]]; then
  "${VENV_DIR}/bin/python" -m pip install -e "${PROJECT_DIR}/vendor/Rapid-MLX[dev]"
else
  echo "warning: vendor/Rapid-MLX is not initialized; run git submodule update --init" >&2
fi

echo "Environment ready: ${VENV_DIR}"

