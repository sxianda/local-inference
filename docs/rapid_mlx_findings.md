# Rapid-MLX Baseline Findings

Status: **not yet measured**

## Reproducibility

- Rapid-MLX tag:
- Rapid-MLX commit:
- Python and dependency versions:
- Model ID and quantization:
- Exact command and sampling settings:

## Compatibility matrix

| Gate | 4B | 9B | Qwen3.8-27B | Evidence |
|---|---:|---:|---:|---|
| Model loads | pending | pending | pending | |
| Chat Completions | pending | pending | pending | |
| Responses non-streaming | pending | pending | pending | |
| Responses SSE | pending | pending | pending | |
| Tool calls | n/a | pending | pending | |
| Codex tool loop | n/a | pending | pending | |
| Prefix reuse | n/a | pending | pending | |
| Hybrid cache safe | n/a | n/a | pending | |

## Performance

| Scenario | Cold TTFT | Warm TTFT | Prompt TPS | Decode TPS | Cache reuse | Peak memory |
|---|---:|---:|---:|---:|---:|---:|
| Short decode | | | | | | |
| 7K multi-turn | | | | | | |
| 17K cold/warm | | | | | | |
| Coding task | | | | | | |

## Errors and fallbacks

Record parser failures, cache fallbacks, retries, malformed SSE, and generation errors with links to
sanitized result files and GitHub Issues.

## Decision

Choose exactly one after Issues 1-7 have evidence:

- Keep pinned upstream unchanged.
- Keep upstream plus a thin integration wrapper.
- Maintain a focused fork for model architecture, hybrid cache, tool parser, or DFlash2 changes.

