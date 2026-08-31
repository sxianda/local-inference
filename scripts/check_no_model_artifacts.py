#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

BLOCKED_SUFFIXES = {".safetensors", ".gguf", ".onnx", ".bin"}
MAX_TRACKED_BYTES = 20 * 1024 * 1024


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    )
    violations: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode())
        path = root / relative
        if relative.suffix.lower() in BLOCKED_SUFFIXES:
            violations.append(f"blocked model artifact: {relative}")
        if path.is_file() and path.stat().st_size > MAX_TRACKED_BYTES:
            violations.append(f"tracked file exceeds 20 MiB: {relative}")
    if violations:
        print("\n".join(violations))
        return 1
    print("No model artifacts or oversized files are tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

