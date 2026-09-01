# Comparative Benchmark Suite

The suite separates protocol correctness, model behavior, cache behavior, and throughput so a fast
short completion cannot conceal a cache or tool-loop failure.

| Script | Purpose |
|---|---|
| `bench_api.py` | short Responses throughput and engine identity |
| `bench_multiturn.py` | lightweight append-only Chat timing |
| `bench_cache.py` | long prefill, append history, branch history, and recurrent-cache safety |
| `bench_tools.py` | repeated fixed-schema Responses function calls |
| `bench_tool_schema_change.py` | alternating strict tool schemas |
| `aggregate_results.py` | cross-model comparison and acceptance gates |

Only sanitized outputs are committed. Generated text, private prompts, absolute code paths, raw
logs, and authentication data are excluded. `comparison.json` is the current machine-readable
summary; individual JSON files retain request-level evidence.

TTFT and decode throughput are directly measured. `estimated_shared_prompt_ratio` describes logical
overlap between requests and is deliberately not labeled a cache hit. Rapid-MLX 0.13.2 does not
expose recurrent prefix-hit tokens, so `runtime_cache_hit_tokens` remains null even though the text
scheduler logs recurrent boundary snapshots and prompt-cache saves.

The aggregate uses the Qwen3.8-27B `*-text-lane.json` results. The tracked registry supplies
`--no-mllm`, which prevents text-only requests from being serialized through the automatically
selected MLLM lane. The original `qwen38-27b-*.json` files remain committed as the failing automatic
lane baseline and are not silently overwritten.
