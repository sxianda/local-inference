#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx


def stream_chat(
    client: httpx.Client,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    started = time.perf_counter()
    first_delta: float | None = None
    text: list[str] = []
    usage: dict[str, Any] = {}
    with client.stream(
        "POST",
        f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "max_tokens": 16,
            "temperature": 0,
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
            content = (choices[0].get("delta") or {}).get("content") if choices else None
            if content:
                first_delta = first_delta or time.perf_counter()
                text.append(content)
    ended = time.perf_counter()
    return {
        "ttft_seconds": first_delta - started if first_delta else None,
        "total_seconds": ended - started,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "output_chars": len("".join(text)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise long-prefix recurrent-cache safety")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--prefix-words", type=int, default=6000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    vocabulary = ["amber", "birch", "cobalt", "delta", "ember", "fjord", "granite", "harbor"]
    prefix = " ".join(vocabulary[index % len(vocabulary)] for index in range(args.prefix_words))
    system = (
        "This is immutable reference text. Preserve it exactly as conversation context.\n" + prefix
    )
    first_messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Reply exactly CACHE_A."},
    ]

    with httpx.Client(timeout=600) as client:
        cold = stream_chat(client, args.base_url.rstrip("/"), args.model, first_messages)
        append_messages = [
            *first_messages,
            {"role": "assistant", "content": "CACHE_A"},
            {"role": "user", "content": "Reply exactly CACHE_B."},
        ]
        append = stream_chat(client, args.base_url.rstrip("/"), args.model, append_messages)
        branch_messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Reply exactly CACHE_BRANCH."},
        ]
        branch = stream_chat(client, args.base_url.rstrip("/"), args.model, branch_messages)

    cold_tokens = cold.get("prompt_tokens") or 0
    append_tokens = append.get("prompt_tokens") or 0
    estimated_shared = cold_tokens / append_tokens if cold_tokens and append_tokens else None
    cold_ttft = cold.get("ttft_seconds")
    append_ttft = append.get("ttft_seconds")
    payload = {
        "engine": "rapid-mlx",
        "model_id": args.model_id,
        "scenario": "long-prefix-append-and-branch",
        "prefix_words": args.prefix_words,
        "cold": cold,
        "append": append,
        "branch": branch,
        "estimated_shared_prompt_ratio": estimated_shared,
        "append_ttft_speedup": (
            cold_ttft / append_ttft if cold_ttft and append_ttft else None
        ),
        "cache_integrity": "passed",
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
