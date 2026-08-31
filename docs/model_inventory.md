# Local Model Inventory

This is a reproducibility record, not a source of model weights. Model files remain outside Git in
`/Users/soleilx/Models`; no checksum, prompt, credential, or machine-local configuration is committed.

| Stable ID | Local directory | Role | Source | Validation |
|---|---|---|---|---|
| `dev-4b` | `Qwen3.5-4B-MLX-4bit` | HTTP/API development | ModelScope `lmstudio-community/Qwen3.5-4B-MLX-4bit` | passed |
| `agent-9b` | `Qwen3.5-9B-MLX-4bit` | Codex/Agent validation | ModelScope `lmstudio-community/Qwen3.5-9B-MLX-4bit` | passed |
| `qwen38-27b` | `Qwen3.8-27B-4bit` | production baseline | existing local asset | passed |
| `qwen38-dflash2-q4` | `Qwen3.8-27B-DFlash2-4bit` | gated DFlash2 target | existing local asset | passed |
| `qwen38-dflash2-bf16` | `Qwen3.8-27B-DFlash2` | gated drafter | existing local asset | passed without a tokenizer; target tokenizer is reused |

## Acquisition behavior

`scripts/download_models.py` skips an already-valid destination and refuses to overwrite an
invalid existing directory. New downloads go into `/Users/soleilx/Models/.downloads`, use
ModelScope first and Hugging Face second, and are moved into their registered final path only after
validation succeeds. A failed staging directory is retained for diagnosis.

Validation confirms readable `config.json`, tokenizer metadata when required, every shard named by
`model.safetensors.index.json`, at least one weight file, and non-empty safetensors files.

Recorded 2026-08-31 on Apple M5 Max, using the project-local Python 3.12 environment.
