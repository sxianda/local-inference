#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from local_inference.benchmark import BenchmarkResult


def engine_metadata(root: Path) -> tuple[str, str]:
    vendor = root / "vendor/Rapid-MLX"
    version = "unknown"
    commit = "unknown"
    try:
        version = subprocess.run(
            [str(root / ".venv/bin/rapid-mlx"), "--version"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=vendor, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return version, commit


def usage_value(payload: dict[str, Any], key: str) -> int:
    usage = payload.get("usage") or {}
    value = usage.get(key, 0)
    return int(value) if isinstance(value, int | float) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark a running Rapid-MLX Responses endpoint")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-name", default="default")
    parser.add_argument("--quantization", default="unknown")
    parser.add_argument("--scenario", default="short-responses")
    parser.add_argument(
        "--prompt", default="Write a Python function that computes Fibonacci numbers."
    )
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    version, commit = engine_metadata(root)
    started = time.perf_counter()
    error = None
    payload: dict[str, Any] = {}
    try:
        with httpx.Client(timeout=600) as client:
            response = client.post(
                f"{args.base_url.rstrip('/')}/responses",
                json={
                    "model": args.model_name,
                    "input": args.prompt,
                    "max_output_tokens": args.max_output_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        error = str(exc)
    total = time.perf_counter() - started
    prompt_tokens = usage_value(payload, "input_tokens")
    completion_tokens = usage_value(payload, "output_tokens")
    result = BenchmarkResult(
        engine="rapid-mlx",
        engine_version=version,
        engine_commit=commit,
        model_id=args.model_id,
        model_name=args.model_name,
        quantization=args.quantization,
        scenario=args.scenario,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        ttft_seconds=None,
        total_seconds=total,
        prompt_tps=None,
        decode_tps=(completion_tokens / total) if completion_tokens and total else None,
        cache_hit_tokens=None,
        peak_memory_gb=None,
        error=error,
    ).to_dict()
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
