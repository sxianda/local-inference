# Rapid-MLX Local Inference Service
## Validation, Integration, and Development Plan

## 0. Project Objective

Build a local Apple-Silicon-native inference service around **Rapid-MLX**.

Long-term goals:

- OpenAI-compatible HTTP APIs.
- Codex Responses API compatibility.
- Efficient long-context and multi-turn prefix reuse.
- Replaceable local models.
- Support for Qwen hybrid recurrent-cache architectures.
- Optional speculative decoding.
- Local-only operation by default.
- Monitoring of TTFT, prompt TPS, decode TPS, cache reuse and memory.
- Future ComfyUI and local-agent integration.
- Stable API surface independent of model architecture.

The first implementation should **validate Rapid-MLX rather than immediately building another inference engine from scratch**.

---

## 1. Existing Hardware and Runtime Baseline

Development machine:

```text
MacBook Pro
Apple M5 Max
40-core GPU
64 GB unified memory
2 TB SSD
```

Current production candidate:

```text
Target:
Qwen3.8-27B MLX Q4

Path:
/Users/soleilx/Models/Qwen3.8-27B-4bit

DFlash2 drafter:
/Users/soleilx/Models/Qwen3.8-27B-DFlash2-4bit
```

Existing environment:

```text
conda env: qwen38
Python: 3.12
```

Do **not** install Rapid-MLX into this environment initially. Use an isolated environment so the already-working MLX-VLM setup remains intact.

---

## 2. Existing Qwen3.8 Performance Baseline

### Plain autoregressive Qwen3.8-27B Q4

```text
Prompt: 41 tokens
Prompt TPS: 261.8 tok/s
Decode: 32.95 tok/s
Peak memory: 16.4 GB
```

### Qwen3.8-27B Q4 + DFlash2 BF16

```text
Decode: 54.04 tok/s
Peak memory: 21.46 GB
Accepted tokens / round: 3.06
Draft acceptance: ~76%
```

### Qwen3.8-27B Q4 + DFlash2 Q4

```text
Prompt TPS: 339.8 tok/s
Decode: 59.68 tok/s
Peak memory: 18.69 GB
Accepted tokens / round: 3.07
Draft acceptance: ~75%
Speedup vs plain AR: ~1.81x
```

This is currently the preferred B=1 decoding configuration.

---

## 3. Cache Findings

Qwen3.8 uses a hybrid architecture containing conventional attention cache plus recurrent/linear-attention state.

### APC

APC exact-mode works on the direct generation path.

```text
Cold request: ~24.5 s
Warm request: ~4.1 s
matched_tokens: ~16,893
end-to-end speedup: ~5.9x
```

APC is useful for cold sessions, shared static prefixes, fallback recovery, and large common system prompts.

### PromptCacheState

Rolling PromptCacheState gives substantially better conversational reuse.

```text
Turn 1:
TTFT ~7.96 s
cached 0

Turn 2:
TTFT ~0.136 s
cached 7036 / 7067

Turn 3:
TTFT ~0.132 s
cached 7195 / 7227
```

Typical rolling reuse is approximately **99.5%**.

Recommended stack:

```text
L1: PromptCacheState
    rolling current conversation

L2: APC
    cold/shared-prefix/fallback

Decode: DFlash2 Q4
```

---

## 4. Hybrid Cache Rollback Problem

Occasionally MLX-VLM attempts:

```python
cache.trim(n_drop)
```

but the recurrent cache contains `ArraysCache`, which cannot safely be treated as an ordinary trimmable KV cache.

Observed error:

```text
AttributeError:
'ArraysCache' object has no attribute 'trim'
```

Current safe fallback:

```text
normal request
    ↓
PromptCacheState reuse
    ↓
ArraysCache.trim failure?
    ├── no → continue
    └── yes
          ↓
       discard L1 only
          ↓
       preserve APC/messages/models
          ↓
       retry same request once
          ↓
       establish new L1
```

Never fake `ArraysCache.trim()`, and never trim only some layers.

This fallback has been observed working in real multi-turn usage and is acceptable because the failure is infrequent.

---

## 5. Existing MLX-VLM Server Finding

The existing continuous-batching server was tested with APC + DFlash2:

```text
cold TTFT: ~21.4 s
decode: ~40 t/s
warm TTFT: ~21.7 s
APC exact hits: 0
```

The continuous-batching path did not preserve the APC behavior seen with direct `stream_generate`.

Therefore the current custom runtime remains the B=1 latency reference.

Rapid-MLX must be benchmarked rather than assumed faster.

---

## 6. Why Validate Rapid-MLX

Rapid-MLX already covers most infrastructure we would otherwise need to build:

- OpenAI Chat API.
- OpenAI Responses API.
- Codex integration.
- Anthropic API.
- Continuous batching.
- Radix/prefix caching.
- Hybrid recurrent-state snapshots.
- Tool-call parsing.
- Reasoning parsing.
- Structured output.
- Metrics.
- Agent integrations.
- Model aliases and local model paths.

The goal is to determine whether Rapid-MLX can become the base runtime, possibly with a thin local wrapper.

---

# 7. Development Model Strategy

Use three model tiers.

## Tier A — 4B smoke model

Recommended class:

```text
Qwen3.5-4B Q4
```

Use for:

- Server startup.
- HTTP routes.
- SSE streaming.
- Responses API serialization.
- Monitoring.
- Unit/integration test development.
- Error handling.
- CI-style smoke tests.

Do not judge Codex intelligence with this model.

## Tier B — 9B integration model

Recommended class:

```text
Qwen3.5-9B Q4
```

Use as the **main day-to-day Codex/agent development model**.

Use it for:

- Codex protocol.
- Tool calling.
- `apply_patch`.
- Multi-turn agent interactions.
- Prefix-cache testing.
- Responses streaming.
- Shell/tool result loops.
- Retry/error behavior.
- Session logic.
- Monitoring and orchestration.

Why 9B is preferable during development:

- Faster restart/load cycles.
- Lower memory pressure.
- Faster prompt iteration.
- More realistic tool-use capability than 4B.
- Large enough to expose most Codex integration problems.
- Avoids spending 27B runtime on HTTP/schema/debugging mistakes.

The 9B model is for **protocol and agent behavior validation**, not final production-quality coding evaluation.

## Tier C — Qwen3.8-27B production candidate

Use for:

- Real coding quality.
- Hybrid-cache correctness.
- Long contexts.
- Performance measurements.
- Memory measurements.
- Qwen3.8 compatibility.
- DFlash2.
- Final Codex evaluation.

Do not optimize 4B/9B behavior at the expense of 27B correctness.

---

# 8. Recommended Test Pyramid

```text
Layer 1
pytest/unit tests
no model

Layer 2
4B smoke
HTTP/API/server correctness

Layer 3
9B agent integration
Codex/tools

Layer 4
27B production benchmark
performance/hybrid/DFlash
```

Preferred development loop:

```text
unit test
 ↓
4B smoke
 ↓
9B Codex/tool test
 ↓
27B production validation
```

---

# 9. Phase 1 — Install Rapid-MLX From Source

```bash
mkdir -p ~/Projects
cd ~/Projects

git clone https://github.com/raullenchai/Rapid-MLX.git
cd Rapid-MLX

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
pip install -e ".[dev]"
```

Record exact versions:

```bash
python --version
rapid-mlx --version
git rev-parse HEAD
```

Store them in:

```text
docs/environment.md
```

Do not develop against an unidentified moving `main`.

---

# 10. Disable Telemetry Explicitly

```bash
export RAPID_MLX_TELEMETRY=0
rapid-mlx telemetry status
```

All local launcher scripts should explicitly disable telemetry.

---

# 11. Diagnostics

```bash
rapid-mlx doctor
```

Then, if available:

```bash
make smoke
```

Do not proceed to Qwen3.8 until the environment is clean.

---

# 12. Phase 2 — 4B HTTP/API Smoke

Start:

```bash
RAPID_MLX_TELEMETRY=0 rapid-mlx serve qwen3.5-4b-4bit   --host 127.0.0.1   --port 8000
```

Always bind development services to `127.0.0.1`.

Basic tests:

```bash
curl -sS http://127.0.0.1:8000/v1/models | jq .
```

```bash
curl -sS   http://127.0.0.1:8000/v1/chat/completions   -H 'Content-Type: application/json'   -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Reply with exactly: RAPID_MLX_OK"}
    ]
  }' | jq .
```

Responses API:

```bash
curl -sS   http://127.0.0.1:8000/v1/responses   -H 'Content-Type: application/json'   -d '{
    "model": "gpt-5",
    "input": "Reply with exactly: RESPONSES_OK",
    "stream": false
  }' | jq .
```

---

# 13. Responses Streaming Test

Create:

```text
scripts/test_responses_stream.py
```

Verify:

```text
HTTP 200
Content-Type text/event-stream
response.created exists
text deltas arrive incrementally
response.completed exists
no malformed SSE records
```

Streaming must be tested independently from non-streaming.

---

# 14. Phase 3 — 9B Codex Integration

Start:

```bash
RAPID_MLX_TELEMETRY=0 rapid-mlx serve qwen3.5-9b-4bit   --host 127.0.0.1   --port 8000
```

Before adding tuning flags:

```bash
rapid-mlx serve --help
```

Only use flags supported by the installed revision.

---

# 15. Codex Configuration

Before modification:

```bash
cp ~/.codex/config.toml    ~/.codex/config.toml.before-rapid-mlx
```

Do not destroy the existing GPT-5.6 Sol configuration.

Conceptual provider:

```toml
[model_providers.rapid-mlx]
name = "Rapid-MLX (local)"
base_url = "http://127.0.0.1:8000/v1"
```

Then use a dedicated local model/profile:

```toml
model = "default"
model_provider = "rapid-mlx"
```

Inspect the locally installed Codex CLI schema before finalizing exact syntax.

---

# 16. Initial Codex Tests

Create a disposable project:

```text
~/Projects/rapid-mlx-agent-test/
```

Suggested files:

```text
calculator.py
test_calculator.py
README.md
```

Test in this order:

1. Explain one file.
2. Add one simple function.
3. Add a pytest test.
4. Fix a deliberately failing test.
5. Rename one function across two files.
6. Make a small `apply_patch` change.
7. Run tests and react to failure.

Record:

```text
tool calls
malformed tool calls
retries
patch correctness
tests passed
total latency
```

The 9B stage measures **protocol correctness and realistic agent behavior**, not final model quality.

---

# 17. Phase 4 — Qwen3.8 Compatibility Gate

After 4B and 9B work correctly:

```bash
RAPID_MLX_TELEMETRY=0 rapid-mlx serve   /Users/soleilx/Models/Qwen3.8-27B-4bit   --host 127.0.0.1   --port 8000
```

Do **not** enable DFlash on the first test.

Validate plain target-model compatibility first.

Checklist:

```text
[ ] model config loads
[ ] tokenizer loads
[ ] chat template works
[ ] normal text generation works
[ ] streaming works
[ ] long prompt works
[ ] multi-turn prefix reuse works
[ ] tool calls parse correctly
[ ] /v1/responses works
[ ] Codex executes a simple tool loop
[ ] no ArraysCache trim crash
```

---

# 18. Do Not Port Existing Cache Logic Prematurely

Current custom runtime:

```text
PromptCacheState
+
APC exact snapshots
```

Rapid-MLX:

```text
radix/prefix cache
+
hybrid recurrent-state snapshots
```

First measure Rapid-MLX's native behavior.

Only port custom fallback logic if Qwen3.8 reproduces a genuine failure.

---

# 19. Benchmark Harness

Create:

```text
benchmarks/
  bench_b1_decode.py
  bench_long_prefill.py
  bench_multiturn_cache.py
  bench_responses.py
  bench_tools.py
  bench_codex_task.py
```

Each result should record:

```json
{
  "engine": "rapid-mlx",
  "git_commit": "...",
  "model": "...",
  "quantization": "...",
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "ttft": 0,
  "total_seconds": 0,
  "prompt_tps": 0,
  "decode_tps": 0,
  "cache_hit_tokens": 0,
  "peak_memory_gb": 0
}
```

Save results as JSON.

---

# 20. Comparative Benchmarks

Compare:

```text
A. Current direct MLX-VLM runtime
B. Rapid-MLX plain Qwen3.8
C. Later: Rapid-MLX + speculative mode
```

### Short prompt

```text
~40 input tokens
1024 output tokens
```

Purpose: decode throughput.

### Medium multi-turn

```text
~7K prompt
3 append-only turns
```

Purpose: rolling-prefix reuse and TTFT.

### Long context

```text
~17K tokens
cold + warm
```

Purpose: prefill and prefix cache.

### Coding

Reuse the coding prompt that previously reached roughly:

```text
59.7 t/s
```

with the custom DFlash2 Q4 path.

---

# 21. Acceptance Criteria

## Cache

For append-only multi-turn conversations:

```text
warm TTFT must be substantially lower than cold TTFT
```

Initial gate:

```text
>= 10x TTFT reduction
```

Desired prefix reuse:

```text
>95%
```

Current custom-runtime target:

```text
~99.5% rolling reuse
~0.13 s warm TTFT
```

## Decode

Existing baselines:

```text
Plain AR: ~33 t/s
DFlash2 Q4: ~60 t/s
```

Interpretation:

```text
<25 t/s     investigate major overhead
30–40 t/s   reasonable plain-engine result
>40 t/s     good
~60 t/s     matches custom DFlash2 path
```

Correctness and Codex compatibility come before speculative-speed optimization.

---

# 22. Monitoring Plan

Final local monitor should expose:

```text
active model
server uptime
active requests
queue depth
prompt tokens
completion tokens
TTFT
prompt TPS
decode TPS
cache hit/reuse
current/peak memory
fallback count
generation errors
```

If Rapid-MLX does not expose a metric reliably, calculate it at the gateway/client layer.

---

# 23. DFlash Strategy

Do not enable DFlash for initial Codex testing.

Initial path:

```text
Codex
   ↓
Rapid-MLX normal engine
   ↓
tool calls + prefix cache
```

Later:

```text
             ┌── Codex server
             │   normal engine
clients ─────┤
             │
             └── fast-generation server
                 DFlash
                 B=1
```

Or extend Rapid-MLX later so DFlash can coexist with the necessary tool path.

Already-available assets:

```text
target:
Qwen3.8-27B Q4

drafter:
Qwen3.8-27B-DFlash2 Q4
```

Do not redownload or discard them.

---

# 24. Qwen3.8 Tool Parser Work

If text inference works but Codex tool calls fail, isolate parser work.

Required tests:

```text
single function call
multiple sequential calls
JSON arguments
escaped strings
multiline arguments
apply_patch
tool result → assistant continuation
malformed tool recovery
```

Add golden tests before parser changes.

---

# 25. Hybrid Cache Investigation

For Qwen3.8 explicitly test:

```text
strict append-only conversation
minor suffix changes
long shared system prompt
branching history
tool-schema changes
```

Record whether Rapid-MLX:

```text
reuses prefix
recomputes safely
snapshots recurrent state
throws trim errors
```

If native behavior is correct, keep it.

If a trim-class failure occurs, prefer exact recurrent-state restoration or safe cache discard/re-prefill. Never fake recurrent trimming.

---

# 26. Model Abstraction

After Qwen3.8 works, create a launcher/config layer outside Rapid-MLX source.

Example:

```yaml
models:

  qwen38-27b:
    model: /Users/soleilx/Models/Qwen3.8-27B-4bit
    mode: codex
    port: 8000

  dev-9b:
    model: qwen3.5-9b-4bit
    mode: development
    port: 8000

  future-moe:
    model: /Users/soleilx/Models/Future-MoE-30B
    mode: codex
    port: 8000
```

Clients should use stable model IDs rather than filesystem paths.

---

# 27. Future ~30B MoE Evaluation

For each future model record:

```text
load memory
active-parameter decode speed
cold TTFT
warm TTFT
tool-call quality
Codex task completion
context length
prefix-cache behavior
```

Do not select a model based only on tokens/sec.

For agent workloads, tool correctness, coding quality, and cache efficiency may matter more.

---

# 28. Initial Deliverables

Before optimization, create:

```text
docs/
  environment.md
  rapid_mlx_findings.md

scripts/
  start_dev_4b.sh
  start_dev_9b.sh
  start_qwen38.sh
  stop_server.sh

benchmarks/
  bench_b1.py
  bench_multiturn.py
  bench_long_context.py
  bench_responses.py
  bench_tools.py

results/
  .gitkeep
```

No custom Rapid-MLX fork should be created until a baseline report exists.

---

# 29. Baseline Report

`docs/rapid_mlx_findings.md` must answer:

```text
Rapid-MLX version / commit
Does Qwen3.8 load?
Does /v1/chat/completions work?
Does /v1/responses work?
Does Codex connect?
Do tool calls work?
Does prefix reuse work?
Any hybrid-cache errors?
Cold TTFT?
Warm TTFT?
Prompt TPS?
Decode TPS?
Peak memory?
How does it compare to the existing runtime?
```

Only after this report should architectural modifications begin.

---

# 30. Optimization Roadmap

## P0 — Correctness

```text
Qwen3.8 load
Responses API
tool calling
Codex end-to-end
hybrid-cache safety
```

## P1 — Prefix caching

```text
multi-turn warm TTFT
long shared prefixes
recurrent-state reuse
```

## P2 — Decode speed

```text
B=1 scheduling overhead
sampling overhead
DFlash integration
```

## P3 — Observability

```text
HTTP dashboard
per-request metrics
historical benchmarks
errors/cache statistics
```

## P4 — Model lifecycle

```text
switch Qwen ↔ MoE
model registry
warm-up
memory cleanup
```

## P5 — ComfyUI/local-agent adapters

```text
prompt generation
tag normalization
structured JSON
dataset classification
```

---

# 31. Decision Gate: Keep, Wrap, or Fork Rapid-MLX

Prefer upstream Rapid-MLX unchanged if:

```text
Qwen3.8 works
Codex works
cache performance is competitive
tool correctness is good
```

Create a thin local wrapper if only these are missing:

```text
monitoring
model registry
launch profiles
```

Create a maintained fork only if Qwen3.8 requires changes to:

```text
model architecture
hybrid cache
tool parser
DFlash integration
```

Avoid forking merely to customize UI.

---

# 32. Success Definition

The initial experiment succeeds when:

```text
[ ] clean isolated install
[ ] 4B HTTP smoke passes
[ ] Responses API streaming passes
[ ] 9B Codex performs tool calls
[ ] local Qwen3.8 loads
[ ] Qwen3.8 Chat API works
[ ] Qwen3.8 Responses API works
[ ] Qwen3.8 Codex tool loop works
[ ] no unsafe hybrid cache corruption
[ ] repeated prefixes show meaningful warm-TTFT improvement
[ ] benchmark comparison with current runtime is recorded
```

Only then begin DFlash2 integration and custom monitoring work.

---

# 33. Final Development Recommendation

Use:

| Model tier | Primary role |
|---|---|
| 4B Q4 | HTTP, SSE, unit/smoke, dashboard |
| 9B Q4 | **Main Codex/agent development model** |
| Qwen3.8-27B Q4 | Final quality, performance, hybrid-cache validation |
| Qwen3.8-27B + DFlash2 Q4 | Final B=1 performance optimization |

The 9B model should be the default local agent development model because it preserves a fast iteration loop while remaining large enough to expose realistic Codex/tooling issues.

The 27B model should be brought back whenever work depends on Qwen3.8-specific architecture, long-context behavior, hybrid recurrent cache, DFlash2, production latency, memory, or final coding quality.
