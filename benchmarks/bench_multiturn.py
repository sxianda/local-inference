#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx


def stream_turn(
    client: httpx.Client, base_url: str, model: str, messages: list[dict[str, str]]
) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    first_delta: float | None = None
    text_parts: list[str] = []
    usage: dict[str, Any] = {}
    with client.stream(
        "POST",
        f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        },
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue
            raw = line.removeprefix("data:").strip()
            if raw == "[DONE]":
                break
            event = json.loads(raw)
            if event.get("usage"):
                usage = event["usage"]
            choices = event.get("choices") or []
            if not choices:
                continue
            content = (choices[0].get("delta") or {}).get("content")
            if content:
                if first_delta is None:
                    first_delta = time.perf_counter()
                text_parts.append(content)
    ended = time.perf_counter()
    return "".join(text_parts), {
        "ttft_seconds": (first_delta - started) if first_delta else None,
        "total_seconds": ended - started,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure append-only multi-turn cache behavior")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", default="default")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a concise coding assistant. Preserve all prior constraints.",
        }
    ]
    prompts = [
        "Define a Python dataclass for a benchmark record in under 120 words.",
        "Add two validation invariants to the same design.",
        "Now give one pytest test for the second invariant.",
    ]
    turns: list[dict[str, Any]] = []
    with httpx.Client(timeout=600) as client:
        for index, prompt in enumerate(prompts, start=1):
            messages.append({"role": "user", "content": prompt})
            text, timing = stream_turn(client, args.base_url.rstrip("/"), args.model, messages)
            turns.append({"turn": index, **timing})
            messages.append({"role": "assistant", "content": text})

    cold = turns[0].get("ttft_seconds")
    warm = [turn.get("ttft_seconds") for turn in turns[1:] if turn.get("ttft_seconds")]
    payload = {
        "engine": "rapid-mlx",
        "model_id": args.model_id,
        "scenario": "append-only-multiturn",
        "turns": turns,
        "cold_ttft_seconds": cold,
        "best_warm_ttft_seconds": min(warm) if warm else None,
        "warm_speedup": (cold / min(warm)) if cold and warm else None,
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
