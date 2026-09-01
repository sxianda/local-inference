# Qwen3.8-27B Compatibility and Hybrid Cache Validation

Validation date: 2026-09-01

## Baseline

- Engine: Rapid-MLX 0.13.2 at `7da40670f349f9faa4b690b48be5110953496610`
- Model: `qwen38-27b`, local MLX affine 4-bit checkpoint
- Host: Apple M5 Max, 64 GB unified memory
- Validation port: 8001 because an unrelated service owns 8000

## Passed

- Local absolute-path loading without a Hub download
- Chat Completions and Responses, streaming and non-streaming
- Responses SSE event completion
- structured invalid-request responses
- two queued concurrent client requests
- cancellation and timeout recovery
- branch-prefix and append-prefix requests without cache corruption
- no `ArraysCache.trim` crash
- direct Responses tool call: 5/5 with an unchanged schema

## Failed acceptance thresholds

The 6,000-word long-prefix case produced 8,322 prompt tokens. Cold TTFT was 9.43 seconds; the
append-only request was 10.97 seconds and the branch request was 11.21 seconds. The logical shared
prefix ratio was 99.75%, but there was no runtime speedup (0.86x rather than the required 10x).
Logical overlap must not be mistaken for a measured cache hit.

Rapid-MLX detected the checkpoint as hybrid, but loaded it through the MLLM `ArraysCache` serialized
compatibility path (`max_num_seqs=1`). Every long request logged the vision 8,192-token budget
warning even though the workload was text. This route appears to bypass or fail to restore the
expected recurrent-cache snapshot.

Unchanged tool schemas passed 5/5. Alternating integer and string tool schemas passed 9/12 across
three runs. The failures preserved the correct function name and JSON type but generated
`label_validation` instead of the requested `validation`; this is a semantic model error, not
evidence of a stale schema object. It still fails the strict tool-call success criterion.

## Performance and memory

| Metric | Observed |
|---|---:|
| 256-token short Responses decode | 26.69 tok/s |
| Reference target | ~33 tok/s |
| Metal active memory | 16.06 GB |
| Metal peak memory after long-prefix tests | 19.46 GB |

Rapid-MLX emitted a projected 86% unified-memory utilization warning before model load. The process
remained stable during this bounded suite.

## Metadata inconsistencies

`GET /v1/models` reports the model as a vision lane and omits the `tools` capability, while direct
Responses tool calls work. `/v1/cache/stats` simultaneously reports that the loaded model is
text-only. These inconsistent classifications should be included in an upstream reproduction.

## Decision

Do not change the Rapid-MLX fork yet. Preserve these results as the reproducible baseline and keep
Issue #5 open. The next engineering step is a minimal upstream reproduction focused on Qwen3.8 text
lane selection and recurrent snapshot reuse; any fork patch must start from the pinned commit.
