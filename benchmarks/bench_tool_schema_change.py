#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx

CASES: list[dict[str, Any]] = [
    {
        "name": "lookup_issue",
        "prompt": "Call lookup_issue for issue 7. Do not answer directly.",
        "arguments": {"number": 7},
        "parameters": {
            "type": "object",
            "properties": {"number": {"type": "integer"}},
            "required": ["number"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lookup_label",
        "prompt": "Call lookup_label for label validation. Do not answer directly.",
        "arguments": {"name": "validation"},
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Alternate tool schemas against Responses")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    attempts: list[dict[str, Any]] = []
    with httpx.Client(timeout=600) as client:
        for case in [*CASES, *CASES]:
            tool = {
                "type": "function",
                "name": case["name"],
                "description": "Return the requested local fixture record.",
                "parameters": case["parameters"],
                "strict": True,
            }
            response = client.post(
                f"{args.base_url.rstrip('/')}/responses",
                json={"model": args.model, "input": case["prompt"], "tools": [tool]},
            )
            response.raise_for_status()
            calls = [
                item
                for item in response.json().get("output", [])
                if item.get("type") == "function_call"
            ]
            valid = len(calls) == 1
            actual: dict[str, Any] | None = None
            if valid:
                actual = {
                    "name": calls[0].get("name"),
                    "arguments": json.loads(calls[0].get("arguments", "{}")),
                }
                valid = (
                    actual["name"] == case["name"]
                    and actual["arguments"] == case["arguments"]
                )
            attempts.append({"schema": case["name"], "valid": valid, "actual": actual})

    payload = {
        "engine": "rapid-mlx",
        "model_id": args.model_id,
        "scenario": "responses-tool-schema-change",
        "attempts": attempts,
        "valid": sum(item["valid"] for item in attempts),
        "total": len(attempts),
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if payload["valid"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
