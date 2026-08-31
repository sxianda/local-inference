# Environment Record

## Host

- Machine: MacBook Pro, Apple M5 Max
- GPU: 40 cores
- Unified memory: 64 GB
- Storage: 2 TB SSD
- Model root: `/Users/soleilx/Models`
- Project: `/Users/soleilx/Workspace/Codex/local-inference`
- macOS: 26.5.1 (25F80)
- Python: 3.12.14, project-local `.venv`
- Codex CLI: 0.151.0-alpha.7.2
- GitHub CLI: 2.98.0

## Rapid-MLX pin

These fields are populated after the personal fork submodule is attached:

- Stable release: `v0.13.2`
- Commit SHA: `7da40670f349f9faa4b690b48be5110953496610`
- Fork: `https://github.com/sxianda/Rapid-MLX.git`
- Upstream: `https://github.com/raullenchai/Rapid-MLX.git`

The submodule pointer is the source of truth. Never develop against an unidentified moving branch.

## Verified existing assets

| Path | Format | Approximate disk size |
|---|---|---:|
| `/Users/soleilx/Models/Qwen3.5-4B-MLX-4bit` | MLX 4-bit | 2.9 GB |
| `/Users/soleilx/Models/Qwen3.5-9B-MLX-4bit` | MLX 4-bit | 5.6 GB |
| `/Users/soleilx/Models/Qwen3.8-27B-4bit` | MLX affine 4-bit | 15 GB |
| `/Users/soleilx/Models/Qwen3.8-27B-DFlash2-4bit` | MLX affine 4-bit | 1.0 GB |
| `/Users/soleilx/Models/Qwen3.8-27B-DFlash2` | BF16 | 3.6 GB |

The 4B and 9B models were acquired from ModelScope on 2026-08-31. Both passed JSON,
tokenizer, shard-index, shard-presence, and non-empty-weight validation before their staging
directories were atomically renamed into place. See [model_inventory.md](model_inventory.md).

The existing `qwen38` Conda environment is a protected reference and is not modified by this
project.
