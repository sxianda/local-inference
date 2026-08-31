# Operations

## Bootstrap

```bash
git submodule update --init --recursive
./scripts/bootstrap.sh
cp config/models.example.yaml config/models.local.yaml
.venv/bin/python scripts/doctor.py
```

## Download development models

Preview without writing:

```bash
.venv/bin/python scripts/download_models.py --dry-run dev-4b agent-9b
```

Download using ModelScope first and Hugging Face as fallback:

```bash
.venv/bin/python scripts/download_models.py dev-4b agent-9b
```

Failed staging directories are intentionally retained under `/Users/soleilx/Models/.downloads`.
Inspect them before manually removing anything.

## Start and stop

```bash
./scripts/start_dev_4b.sh
./scripts/start_agent_9b.sh
./scripts/start_qwen38_27b.sh
./scripts/stop_server.sh
```

Launchers run in the foreground, bind to `127.0.0.1`, and disable telemetry. Pass additional
Rapid-MLX arguments after the launcher options only after checking the pinned CLI's `serve --help`.

## Codex

Apply the idempotent user-level configuration after a Responses smoke test passes:

```bash
.venv/bin/python scripts/configure_codex.py --dry-run
.venv/bin/python scripts/configure_codex.py
codex --strict-config --profile rapid-mlx doctor --summary
codex --profile rapid-mlx -C /path/to/disposable/project
```

The configurator backs up `~/.codex/config.toml` before adding the provider and refuses to replace
conflicting existing provider or profile content.

## Tests and benchmarks

```bash
make check
RAPID_MLX_BASE_URL=http://127.0.0.1:8000/v1 \
  .venv/bin/pytest -m model tests/test_api_smoke.py
.venv/bin/python benchmarks/bench_api.py \
  --model-id dev-4b --quantization MLX-4bit \
  --output results/dev-4b-short-responses.json
```

