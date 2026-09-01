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

The stricter scenario—also requiring an `apply_patch` edit and a cross-file rename—did not pass
reliably. One run completed the repair and edge tests but stopped before the rename; another produced
invalid patch framing and failed to recover. The harness postcondition correctly returned non-zero.
Therefore 9B is validated for fast protocol and simple Agent-loop development, but it is not yet a
reliable floor for multi-step refactors on this setup.

## Operational finding

Port 8000 is currently occupied by an independently managed `omlx-server` requiring authentication.
It was not stopped or modified. Rapid-MLX validation used port 8001 through a temporary Codex config
override, while the intended committed/user profile remains `http://127.0.0.1:8000/v1`. Launching on
the intended port requires the user to free or reconfigure that existing listener. The launcher now
checks the port before loading a model and fails with an ownership-inspection command.

## Decision

Keep Rapid-MLX unchanged. Retain 4B for protocol development and 9B for short Agent loops, but use
27B for the acceptance-quality Codex scenarios. Issue #4 remains open until the full rename and
`apply_patch` fixture passes consistently.
