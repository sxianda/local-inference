#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${PROJECT_DIR}/.venv/bin/python" "${PROJECT_DIR}/scripts/serve_model.py" dev-4b "$@"

