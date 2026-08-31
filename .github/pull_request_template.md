## Linked issue

Closes #

## Change

Describe the smallest implementation slice completed by this PR.

## Evidence

- [ ] `ruff check local_inference scripts tests benchmarks`
- [ ] `pytest -m "not model"`
- [ ] `python scripts/check_no_model_artifacts.py`
- [ ] Model-backed evidence attached when applicable
- [ ] Benchmark JSON is sanitized

## Safety

- [ ] No model weights, credentials, raw prompts, or user Codex configuration are committed
- [ ] Existing `/Users/soleilx/Models` assets are not overwritten
- [ ] Rapid-MLX submodule changes identify the upstream/fork commit

