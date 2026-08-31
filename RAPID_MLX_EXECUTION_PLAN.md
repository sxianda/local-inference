# Rapid-MLX Local Inference Execution Plan

## Objective

Validate a pinned Rapid-MLX release as the base of a local OpenAI-compatible inference service on
an M5 Max MacBook Pro with 64 GB unified memory. The service must support Chat Completions,
Responses, streaming, Codex tool loops, safe Qwen3.8 hybrid-cache reuse, and reproducible
benchmarks before any engine fork is modified.

## Repository and GitHub workflow

The public integration repository tracks scripts, tests, results, and documentation. The personal
Rapid-MLX fork is mounted at `vendor/Rapid-MLX` as a Git submodule and is pinned to an exact stable
release commit. Work is tracked under the `Rapid-MLX Validation v1` milestone:

1. Repository and environment bootstrap.
2. Model acquisition and registry.
3. 4B HTTP/Responses smoke validation.
4. 9B Codex/Agent integration.
5. Qwen3.8-27B compatibility and hybrid cache.
6. Comparative benchmark suite.
7. Baseline findings and keep/wrap/fork decision.
8. DFlash2 optimization, gated on Issues 1-7.

Each issue uses `feat/issue-<n>-<name>`, links a PR, includes evidence, and squash-merges after local
verification. Changes to Rapid-MLX use a fork branch based on the pinned SHA; the integration PR
then updates the submodule pointer.

## Model registry and acquisition

All weights are stored under `/Users/soleilx/Models`:

| Stable ID | Absolute path | Role |
|---|---|---|
| `dev-4b` | `/Users/soleilx/Models/Qwen3.5-4B-MLX-4bit` | HTTP/API smoke |
| `agent-9b` | `/Users/soleilx/Models/Qwen3.5-9B-MLX-4bit` | Codex/Agent development |
| `qwen38-27b` | `/Users/soleilx/Models/Qwen3.8-27B-4bit` | production validation |
| `qwen38-dflash2-q4` | `/Users/soleilx/Models/Qwen3.8-27B-DFlash2-4bit` | speculative drafter |
| `qwen38-dflash2-bf16` | `/Users/soleilx/Models/Qwen3.8-27B-DFlash2` | drafter reference |

The downloader stages data under `/Users/soleilx/Models/.downloads`, tries ModelScope first, checks
configuration, tokenizer, safetensors index, shards, and zero-length files, then atomically renames
the directory. Hugging Face is used only after a ModelScope failure. Existing valid directories are
skipped; existing invalid paths are never overwritten.

## Gated implementation

### Phase 1 — environment

- Initialize the submodule at the recorded stable SHA.
- Create `.venv` with Python 3.12 and install this project plus `vendor/Rapid-MLX[dev]` editable.
- Run Rapid-MLX doctor, Ruff, no-model pytest, and the model-artifact guard.
- Record Python, macOS, Rapid-MLX tag/SHA, MLX versions, and Codex version.

### Phase 2 — 4B protocol smoke

- Download `dev-4b`, launch on `127.0.0.1:8000`, and disable telemetry.
- Validate `/v1/models`, Chat Completions, non-streaming Responses, streaming SSE, malformed input,
  cancellation, timeout, and basic concurrency.
- Do not use this phase to judge coding quality.

### Phase 3 — 9B Codex/Agent

- Download and launch `agent-9b`.
- Configure the user-level Codex provider and separate `rapid-mlx` profile without changing the
  existing GPT-5.6 Sol default.
- Run file explanation, function edit, test generation, failing-test repair, cross-file rename,
  `apply_patch`, shell/tool result continuation, malformed tool recovery, and multi-turn tests.

### Phase 4 — Qwen3.8-27B compatibility

- Start the existing target model without DFlash2.
- Validate load, tokenizer/template, Chat, Responses, streaming, tools, long prompts, strict
  append-only conversations, branched history, and tool-schema changes.
- Record recurrent-state restoration behavior. On any trim-class failure, safely discard/re-prefill
  the affected cache; never emulate partial `ArraysCache.trim` behavior.

### Phase 5 — benchmarks and decision

- Compare the current direct MLX-VLM runtime and Rapid-MLX with identical prompts and sampling.
- Store sanitized JSON for short decode, 7K multi-turn, 17K cold/warm, Responses, tools, and Codex
  tasks.
- Require at least 10x warm/cold TTFT improvement and more than 95% append-only prefix reuse.
- Use ~33 tok/s as the plain 27B reference and ~60 tok/s as the later DFlash2 Q4 target.
- Publish `docs/rapid_mlx_findings.md` and decide: keep upstream, add a thin wrapper, or maintain a
  focused fork. Only then enable Issue 8.

## Stable interfaces

The local service root is `http://127.0.0.1:8000`; clients use `/v1/models`,
`/v1/chat/completions`, and `/v1/responses`. Codex uses the Responses wire API. Benchmark records
must include the engine version/commit, stable model ID, quantization, token counts, TTFT, total
time, prompt/decode TPS, cache hits, peak memory, tool validity, and error state.

