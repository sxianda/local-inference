#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${PROJECT_DIR}/.run/rapid-mlx.pid"

if [[ ! -f "${PID_FILE}" ]]; then
  echo "No managed Rapid-MLX server PID file found."
  exit 0
fi

PID="$(tr -d '[:space:]' < "${PID_FILE}")"
if [[ ! "${PID}" =~ ^[0-9]+$ ]]; then
  echo "error: invalid PID file: ${PID_FILE}" >&2
  exit 1
fi
if ! kill -0 "${PID}" 2>/dev/null; then
  echo "Stale PID ${PID}; removing PID file."
  rm "${PID_FILE}"
  exit 0
fi

COMMAND="$(ps -p "${PID}" -o command=)"
if [[ "${COMMAND}" != *rapid-mlx* ]]; then
  echo "error: PID ${PID} is not a Rapid-MLX process; refusing to signal it" >&2
  exit 1
fi

kill -TERM "${PID}"
echo "Sent SIGTERM to Rapid-MLX PID ${PID}."

