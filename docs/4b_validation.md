# 4B API Validation

Validation date: 2026-08-31

## Baseline

- Host: Apple M5 Max, 64 GB unified memory
- Engine: Rapid-MLX 0.13.2 at `7da40670f349f9faa4b690b48be5110953496610`
- Stable model ID: `dev-4b`
- Model path: `/Users/soleilx/Models/Qwen3.5-4B-MLX-4bit`
- Binding: `127.0.0.1:8000`
- Runtime: MLX 0.32.2, Python 3.12.14

## Results

The model loaded from its absolute local path without an implicit Hub download. All six model-backed
tests passed:

1. model discovery and non-streaming Responses;
2. non-streaming and streaming Chat Completions;
3. Responses SSE event ordering from `response.created` through `response.completed`;
4. structured invalid-request errors;
5. two simultaneous client requests;
6. stream cancellation and client timeout followed by a successful health request.

The server log confirmed that cancellation aborted the orphaned scheduler request. The model is
classified by Rapid-MLX as an MLLM using `ArraysCache`, so the two concurrent requests are accepted
and queued but generation is serialized (`max_num_seqs=1`). This is adequate for protocol smoke
work, but it is not evidence of multi-sequence throughput.

## Sanitized measurements

| Scenario | Result |
|---|---:|
| 128-token short Responses decode | 105.69 tok/s |
| Three append-only turns, best warm TTFT | 79 ms |
| Warm/cold TTFT ratio in this short prompt test | 1.52x |
| Responses tool-call serialization | 3/3 valid |

The short-prompt cache test is intentionally not compared with the 10x long-prefix acceptance
threshold; it does not contain enough prefill work to measure that criterion. The committed JSON
files contain timings and engine identity only, with no generated text or private prompts.

## Decision

The 4B protocol baseline passes. It is suitable for fast API, SSE, cancellation, error-path, and
tool-schema development. Proceed to the 9B Codex/Agent stage without changing Rapid-MLX.
