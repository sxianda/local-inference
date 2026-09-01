# 9B Codex/Agent Validation

Validation dates: 2026-08-31 and 2026-09-01

## Baseline

- Engine: Rapid-MLX 0.13.2 at `7da40670f349f9faa4b690b48be5110953496610`
- Model: `agent-9b`, Qwen3.5-9B MLX 4-bit
- Codex CLI: 0.151.0-alpha.7.2, Responses wire protocol
- Profile: user-level `rapid-mlx`; default GPT-5.6 Sol configuration unchanged

## Configuration result

The provider and overlay parse under `--strict-config`. The overlay selects `agent-9b`, disables
reasoning for deterministic development tasks, and disables unrelated App/plugin tools. This reduced
the tool list from 368 to 10 and a one-turn prompt from roughly 150,000 input tokens to roughly
7,700. A basic Codex Responses request then completed in seconds rather than minutes.

The configurator created a timestamped backup before changing `~/.codex/config.toml`. The committed
repository contains only the generator and tests, never the user's configuration or backup.

## Agent results

The 9B model passed Chat/Responses/SSE protocol tests, five of five direct Responses tool-call
serialization attempts, and a simple disposable Agent repair:

- inspected both Python files;
- ran the failing test and read its result;
- fixed the arithmetic error;
- added edge cases in the second file;
- reran three tests successfully;
- completed multiple shell/tool-result turns.

The stricter scenario initially failed because the prompt asked for `apply_patch` as a Responses
function. Codex expects a different item type for its native patch tool, while Rapid-MLX deliberately
advertises `apply_patch_tool_type=null` for local fallback models and instructs them to invoke the
local executable through `exec_command`. The 9B model also defaulted to GNU-style numbered hunk
headers, which Codex's patch grammar rejects.

The committed fixture now states the actual local contract: call `apply_patch` through
`exec_command`, start with `*** Begin Patch`, use `*** Update File:` sections and unnumbered `@@`
hunks, and end with `*** End Patch`. With that model-visible grammar, the bounded 9B validation
repaired the arithmetic bug, renamed the function across both files, added negative-number tests,
used shell/tool-result loops, and passed all three postcondition tests. No Rapid-MLX code change was
required. The successful bounded run reported 45,359 total tokens; this is suitable for development
validation but reinforces using explicit, narrow tasks on 9B.

Sanitized evidence: [agent-9b-codex-fixture.json](../results/agent-9b-codex-fixture.json)

## Operational finding

Port 8000 is currently occupied by an independently managed `omlx-server` requiring authentication.
It was not stopped or modified. Rapid-MLX validation used port 8001 through a temporary Codex config
override, while the intended committed/user profile remains `http://127.0.0.1:8000/v1`. Launching on
the intended port requires the user to free or reconfigure that existing listener. The launcher now
checks the port before loading a model and fails with an ownership-inspection command.

## Decision

Keep Rapid-MLX unchanged. Retain 4B for protocol development, use 9B for bounded Agent loops with
the explicit local patch grammar, and use 27B for less constrained acceptance-quality Codex tasks.
The successful fixture closes Issue #4 without introducing a maintained fork divergence.
