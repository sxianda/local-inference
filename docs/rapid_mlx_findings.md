# Rapid-MLX Baseline Findings

Status: **baseline complete; pinned upstream plus thin integration wrapper selected**

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
| Codex multi-step refactor | n/a | pass | pending | 9B report |
| Long-prefix integrity | n/a | n/a | pass | no state corruption/crash |
| Long-prefix runtime reuse | n/a | n/a | pass | 22.91x on the text lane |
| Alternating tool schemas | n/a | n/a | 9/12 | 27B schema runs |

## Performance

| Model/scenario | Cold TTFT | Warm TTFT | Decode TPS | Tool success | Peak Metal memory |
|---|---:|---:|---:|---:|---:|
| 4B short Responses | n/a | n/a | 105.69 | 3/3 | not recorded |
| 9B short Responses | n/a | n/a | 76.11 | 5/5 | not recorded |
| 27B automatic MLLM lane | 9.43 s | 10.97 s | 26.69 | 5/5 fixed schema | 19.46 GB |
| 27B forced text lane | 9.20 s | 0.40 s | 32.94 | 5/5 fixed schema | not remeasured |

Automatic routing failed both the decode reference and warm-TTFT gate. Adding the existing
`--no-mllm` flag moved the checkpoint onto Rapid-MLX's hybrid text scheduler: the approximately
33 tok/s decode reference was reached (32.94 tok/s), and the identical 8,322-token append workload
improved from 9.20 seconds cold to 0.40 seconds warm (22.91x). The logical prefix overlap remained
99.75%, and the scheduler logs confirmed boundary snapshots and prompt-cache saves.

## Confirmed gaps and mitigations

1. The Qwen3.8 checkpoint is detected as hybrid but routed through the serialized MLLM
   `ArraysCache` path with `max_num_seqs=1`.
2. Text-only long prompts log a vision 8,192-token budget warning.
3. `/v1/models` identifies a vision lane and omits tools, direct tool calls nevertheless work, and
   `/v1/cache/stats` calls the same loaded model text-only.
4. The automatic MLLM lane provides no recurrent-state TTFT improvement; the explicit text lane
   restores boundary snapshots and passes at 22.91x.
5. The 9B Codex profile must disable unrelated plugin/App tools; otherwise the tool inventory grows
   from 10 to 368 and the first prompt approaches 150,000 input tokens.
6. Local fallback models must invoke the `apply_patch` executable through `exec_command` using
   Codex's unnumbered `@@` patch grammar; treating it as a Responses function is unsupported.
7. Port 8000 is occupied by a separately managed authenticated `omlx-server`; Rapid-MLX validation
   used port 8001 without changing that process.

No `ArraysCache.trim` crash, cache-state corruption, malformed SSE sequence, or post-cancellation
health failure occurred in the bounded runs.

## Decision

**Keep pinned upstream plus a thin integration wrapper.**

The main repository's model registry supplies `--no-mllm` for `qwen38-27b`. This is an existing,
audited Rapid-MLX override; it selects the hybrid text scheduler without changing engine code. The
wrapper now passes the API, recurrent-cache, TTFT, prefix-overlap, and decode-reference gates.

The personal fork remains available for upstream experiments, but no maintained divergence is
justified by the measured baseline. The automatic lane metadata inconsistency should be reported
upstream with both result files. A fork patch is considered only if a future checkpoint cannot be
correctly served through supported launch/configuration options.

## DFlash2 gate

The first seven validation milestones now pass. DFlash2 may proceed through its own Issue #8 branch;
no DFlash2 result or 60 tok/s claim is made in this baseline decision.

Detailed evidence:

- [4B validation](4b_validation.md)
- [9B Codex validation](9b_codex_validation.md)
- [9B Codex fixture result](../results/agent-9b-codex-fixture.json)
- [Qwen3.8-27B validation](qwen38_27b_validation.md)
- [benchmark suite](benchmark_suite.md)
- machine-readable [comparison](../results/comparison.json)
