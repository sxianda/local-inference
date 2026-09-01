# Rapid-MLX Baseline Findings

Status: **baseline complete; focused fork work required before DFlash2**

Validation dates: 2026-08-31 through 2026-09-01

## Reproducibility

- Rapid-MLX tag: `v0.13.2`
- Rapid-MLX commit: `7da40670f349f9faa4b690b48be5110953496610`
- Python: 3.12.14 in the repository `.venv`
- MLX: 0.32.2; mlx-lm: 0.31.3; mlx-vlm: 0.6.16
- Host: Apple M5 Max, 40-core GPU, 64 GB unified memory
- Models: `dev-4b`, `agent-9b`, and `qwen38-27b`, all local MLX 4-bit assets
- Model root: `/Users/soleilx/Models`

Development models were acquired with ModelScope as the primary source and validated before atomic
installation. Hugging Face remains a failure-only fallback.

## Compatibility matrix

| Gate | 4B | 9B | Qwen3.8-27B | Evidence |
|---|---:|---:|---:|---|
| Model loads from absolute path | pass | pass | pass | environment/model inventory |
| Chat Completions | pass | pass | pass | model API suite |
| Responses non-streaming | pass | pass | pass | model API suite |
| Responses SSE | pass | pass | pass | model API suite |
| Cancellation and timeout recovery | pass | pass | pass | model API suite |
| Fixed-schema tool calls | 3/3 | 5/5 | 5/5 | sanitized tool JSON |
| Codex simple repair loop | n/a | pass | not run | 9B report |
| Codex multi-step refactor | n/a | fail | pending | 9B report |
| Long-prefix integrity | n/a | n/a | pass | no state corruption/crash |
| Long-prefix runtime reuse | n/a | n/a | fail | 0.86x warm/cold TTFT |
| Alternating tool schemas | n/a | n/a | 9/12 | 27B schema runs |

## Performance

| Model/scenario | Cold TTFT | Warm TTFT | Decode TPS | Tool success | Peak Metal memory |
|---|---:|---:|---:|---:|---:|
| 4B short Responses | n/a | n/a | 105.69 | 3/3 | not recorded |
| 9B short Responses | n/a | n/a | 76.11 | 5/5 | not recorded |
| 27B 256-token Responses | n/a | n/a | 26.69 | 5/5 fixed schema | 19.46 GB |
| 27B 8,322-token append | 9.43 s | 10.97 s | n/a | n/a | 19.46 GB |

The 27B reference decode target of approximately 33 tok/s was not reached. Its 26.69 tok/s result is
about 81% of that reference. More importantly, the required 10x warm TTFT improvement was not
present. The logical prompt overlap was 99.75%, but runtime speedup was 0.86x; logical overlap is not
a cache hit metric.

## Confirmed implementation gaps

1. The Qwen3.8 checkpoint is detected as hybrid but routed through the serialized MLLM
   `ArraysCache` path with `max_num_seqs=1`.
2. Text-only long prompts log a vision 8,192-token budget warning.
3. `/v1/models` identifies a vision lane and omits tools, direct tool calls nevertheless work, and
   `/v1/cache/stats` calls the same loaded model text-only.
4. Recurrent-state prefix restoration provides no measured TTFT improvement on the reproducible
   append-only workload.
5. The 9B Codex profile must disable unrelated plugin/App tools; otherwise the tool inventory grows
   from 10 to 368 and the first prompt approaches 150,000 input tokens.
6. Port 8000 is occupied by a separately managed authenticated `omlx-server`; Rapid-MLX validation
   used port 8001 without changing that process.

No `ArraysCache.trim` crash, cache-state corruption, malformed SSE sequence, or post-cancellation
health failure occurred in the bounded runs.

## Decision

**Maintain a focused Rapid-MLX fork.**

The main repository remains a thin integration and evidence layer. Fork changes are limited to the
gaps that cannot be solved by launch configuration:

1. correct Qwen3.8 text/hybrid lane classification;
2. restore or implement recurrent-state prefix snapshots for append-only and branch histories;
3. expose cache-hit token and snapshot telemetry;
4. reconcile model capability metadata with working tool behavior;
5. add a regression covering the exact 8,322-token append case.

The fork must branch from the pinned v0.13.2 commit. A fork change is accepted only if the main
repository benchmark demonstrates at least 10x warm TTFT improvement, no recurrent-cache corruption,
and stable API/SSE behavior. Upstreamable fixes should be proposed to `raullenchai/Rapid-MLX`; the
main repository then updates only the submodule pointer through a separate PR.

## DFlash2 gate

DFlash2 remains blocked. Issues #4 and #5 are open, so the first seven milestones have not all
passed. Neither DFlash2 launcher integration nor the 60 tok/s target will be claimed until those
gaps are resolved.

Detailed evidence:

- [4B validation](4b_validation.md)
- [9B Codex validation](9b_codex_validation.md)
- [Qwen3.8-27B validation](qwen38_27b_validation.md)
- [benchmark suite](benchmark_suite.md)
- machine-readable [comparison](../results/comparison.json)
