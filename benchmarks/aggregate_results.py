#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ratio(payload: dict[str, Any], numerator: str, denominator: str) -> float | None:
    top = payload.get(numerator)
    bottom = payload.get(denominator)
    if isinstance(top, int | float) and isinstance(bottom, int | float) and bottom:
        return top / bottom
    return None


def aggregate(results_dir: Path) -> dict[str, Any]:
    short = {
        "dev-4b": load(results_dir / "dev-4b-short-responses.json"),
        "agent-9b": load(results_dir / "agent-9b-short-responses.json"),
        "qwen38-27b": load(results_dir / "qwen38-27b-short-responses-text-lane.json"),
    }
    tools = {
        "dev-4b": load(results_dir / "dev-4b-tools.json"),
        "agent-9b": load(results_dir / "agent-9b-tools.json"),
        "qwen38-27b": load(results_dir / "qwen38-27b-tools-text-lane.json"),
    }
    cache_4b = load(results_dir / "dev-4b-multiturn.json")
    cache_27b = load(results_dir / "qwen38-27b-cache-text-lane.json")
    schema_runs = [load(results_dir / "qwen38-27b-tool-schema-change-text-lane.json")]
    schema_valid = sum(int(run["valid"]) for run in schema_runs)
    schema_total = sum(int(run["total"]) for run in schema_runs)

    models = []
    for model in ("dev-4b", "agent-9b", "qwen38-27b"):
        tool_result = tools[model]
        models.append(
            {
                "model_id": model,
                "quantization": short[model].get("quantization", "MLX-4bit"),
                "decode_tps": short[model].get("decode_tps"),
                "short_prompt_tokens": short[model].get("prompt_tokens"),
                "short_completion_tokens": short[model].get("completion_tokens"),
                "tool_success_rate": ratio(
                    tool_result, "tool_calls_valid", "tool_calls_total"
                ),
                "error": short[model].get("error"),
            }
        )

    observed_decode = short["qwen38-27b"].get("decode_tps")
    observed_speedup = cache_27b.get("append_ttft_speedup")
    observed_overlap = cache_27b.get("estimated_shared_prompt_ratio")
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "engine": "rapid-mlx",
        "engine_version": short["qwen38-27b"].get("engine_version"),
        "engine_commit": short["qwen38-27b"].get("engine_commit"),
        "host": "Apple M5 Max, 40-core GPU, 64 GB unified memory",
        "models": models,
        "cache": {
            "dev_4b_short_prompt_speedup": cache_4b.get("warm_speedup"),
            "qwen38_27b_cold_ttft_seconds": cache_27b["cold"]["ttft_seconds"],
            "qwen38_27b_append_ttft_seconds": cache_27b["append"]["ttft_seconds"],
            "qwen38_27b_append_speedup": observed_speedup,
            "logical_shared_prompt_ratio": observed_overlap,
            "runtime_cache_hit_tokens": None,
        },
        "qwen38_tool_schema_success": {
            "valid": schema_valid,
            "total": schema_total,
            "rate": schema_valid / schema_total,
        },
        "acceptance_gates": {
            "qwen38_decode_tps": {
                "reference": 33.0,
                "pass_floor": 31.35,
                "observed": observed_decode,
                "passed": bool(observed_decode and observed_decode >= 31.35),
            },
            "warm_ttft_speedup": {
                "target": 10.0,
                "observed": observed_speedup,
                "passed": bool(observed_speedup and observed_speedup >= 10.0),
            },
            "logical_prefix_overlap": {
                "target": 0.95,
                "observed": observed_overlap,
                "passed": bool(observed_overlap and observed_overlap >= 0.95),
                "note": "Logical overlap only; runtime reuse is not currently observable.",
            },
            "dflash2_decode_tps": {
                "target": 60.0,
                "observed": None,
                "passed": False,
                "note": "Gated until Issues 1-7 pass.",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate sanitized benchmark results")
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/comparison.json"))
    args = parser.parse_args()
    payload = aggregate(args.results_dir)
    rendered = json.dumps(payload, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
