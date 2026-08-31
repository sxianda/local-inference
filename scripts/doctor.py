#!/usr/bin/env python3
from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from local_inference.model_files import validate_model_directory
from local_inference.registry import load_registry


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    failed = False

    rapid = shutil.which("rapid-mlx")
    if rapid:
        result = subprocess.run([rapid, "--version"], capture_output=True, text=True, check=False)
        print(f"Rapid-MLX: {(result.stdout or result.stderr).strip()}")
    else:
        print("Rapid-MLX: missing (run scripts/bootstrap.sh)")
        failed = True

    for model_id, spec in load_registry().items():
        result = validate_model_directory(spec.path, require_tokenizer=spec.requires_tokenizer)
        status = "OK" if result.valid else "MISSING/INVALID"
        print(f"{model_id}: {status} {spec.path}")
        if not result.valid:
            print(f"  {'; '.join(result.errors)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
