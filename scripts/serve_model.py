#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
from pathlib import Path

from local_inference.model_files import validate_model_directory
from local_inference.registry import get_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Rapid-MLX using a registered local model")
    parser.add_argument("model_id")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("rapid_args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = get_model(args.model_id, args.config)
    validation = validate_model_directory(spec.path, require_tokenizer=spec.requires_tokenizer)
    if not validation.valid:
        raise SystemExit(f"invalid model {spec.path}: {'; '.join(validation.errors)}")

    executable = shutil.which("rapid-mlx")
    if executable is None:
        project_cli = Path(__file__).resolve().parents[1] / ".venv/bin/rapid-mlx"
        if not project_cli.is_file():
            raise SystemExit("rapid-mlx not found; run scripts/bootstrap.sh")
        executable = str(project_cli)

    command = [
        executable,
        "serve",
        str(spec.path),
        "--host",
        args.host,
        "--port",
        str(args.port),
        *spec.extra_args,
        *args.rapid_args,
    ]
    runtime_dir = Path(__file__).resolve().parents[1] / ".run"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    pid_path = runtime_dir / "rapid-mlx.pid"
    env = os.environ.copy()
    env["RAPID_MLX_TELEMETRY"] = "0"

    print(f"Starting {args.model_id}: {' '.join(command)}", flush=True)
    process = subprocess.Popen(command, env=env)
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")

    def forward(signum: int, _frame: object) -> None:
        if process.poll() is None:
            process.send_signal(signum)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)
    try:
        return process.wait()
    finally:
        if pid_path.exists() and pid_path.read_text(encoding="utf-8").strip() == str(process.pid):
            pid_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
