# Local Rapid-MLX Inference

Apple-Silicon-native local inference integration built around a pinned Rapid-MLX fork. This
repository owns model acquisition, launch profiles, Codex configuration, API tests, benchmarks,
and findings. Rapid-MLX itself is pinned as `vendor/Rapid-MLX` and remains unchanged until a
reproducible upstream gap is demonstrated.

- Integration repository: <https://github.com/sxianda/local-inference>
- Rapid-MLX fork: <https://github.com/sxianda/Rapid-MLX>

## Safety defaults

- Services listen on `127.0.0.1:8000`.
- Rapid-MLX telemetry is explicitly disabled.
- Model weights live only under `/Users/soleilx/Models` and are blocked from Git.
- Existing Qwen3.8 assets and the `qwen38` Conda environment are never modified.
- Codex keeps the existing cloud model as default; local inference is selected with a profile.

## Quick start

```bash
git submodule update --init --recursive
./scripts/bootstrap.sh
cp config/models.example.yaml config/models.local.yaml
.venv/bin/python scripts/doctor.py
```

Download the 4B and 9B development models. ModelScope is tried first and Hugging Face is the
fallback:

```bash
.venv/bin/python scripts/download_models.py dev-4b agent-9b
```

Start the API smoke model:

```bash
./scripts/start_dev_4b.sh
```

In another terminal:

```bash
RAPID_MLX_BASE_URL=http://127.0.0.1:8000/v1 \
  .venv/bin/pytest -m model tests/test_api_smoke.py
```

See [RAPID_MLX_EXECUTION_PLAN.md](RAPID_MLX_EXECUTION_PLAN.md) and
[docs/operations.md](docs/operations.md) for the gated validation sequence.

## License

Integration code in this repository is Apache-2.0. The Rapid-MLX submodule and model weights keep
their own licenses; they are not relicensed by this project.
