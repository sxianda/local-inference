#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cat >&2 <<'EOF'
DFlash2 is gated until Issues 1-7 and the Rapid-MLX baseline report pass.
Use this launcher only after documenting the supported speculative flags for the pinned release.
EOF
exit 2

