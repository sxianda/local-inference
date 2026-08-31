#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx

TOOL = {
    "type": "function",
    "name": "lookup_issue",
    "description": "Look up a GitHub issue by number.",
    "parameters": {
        "type": "object",
        "properties": {"number": {"type": "integer"}},
        "required": ["number"],
        "additionalProperties": False,
    },
    "strict": True,
}


def function_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    output = payload.get("output") or []
    return [item for item in output if item.get("type") == "function_call"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Responses function-call serialization")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", default="default")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    attempts: list[dict[str, Any]] = []
    with httpx.Client(timeout=600) as client:
        for _ in range(args.iterations):
            started = time.perf_counter()
            error = None
            calls: list[dict[str, Any]] = []
            try:
                response = client.post(
                    f"{args.base_url.rstrip('/')}/responses",
                    json={
                        "model": args.model,
                        "input": "Use lookup_issue to retrieve issue 7. Do not answer directly.",
                        "tools": [TOOL],
                    },
                )
                response.raise_for_status()
                calls = function_calls(response.json())
                for call in calls:
                    arguments = json.loads(call.get("arguments", "{}"))
                    if arguments != {"number": 7}:
                        raise ValueError(f"unexpected arguments: {arguments}")
            except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
                error = str(exc)
            attempts.append(
                {
                    "seconds": time.perf_counter() - started,
                    "valid": error is None and len(calls) == 1,
                    "call_count": len(calls),
                    "error": error,
                }
            )

    valid = sum(bool(item["valid"]) for item in attempts)
    payload = {
        "engine": "rapid-mlx",
        "model_id": args.model_id,
        "scenario": "responses-tool-call",
        "tool_calls_valid": valid,
        "tool_calls_total": args.iterations,
        "attempts": attempts,
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if valid == args.iterations else 1


if __name__ == "__main__":
    raise SystemExit(main())

