from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]
    shard_count: int


def validate_model_directory(path: Path, *, require_tokenizer: bool = True) -> ValidationResult:
    errors: list[str] = []
    if not path.is_dir():
        return ValidationResult(False, (f"missing model directory: {path}",), 0)

    config_path = path / "config.json"
    tokenizer_candidates = (path / "tokenizer_config.json", path / "tokenizer.json")
    if not config_path.is_file():
        errors.append("missing config.json")
    else:
        try:
            json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid config.json: {exc}")
    if require_tokenizer and not any(candidate.is_file() for candidate in tokenizer_candidates):
        errors.append("missing tokenizer_config.json/tokenizer.json")

    index_path = path / "model.safetensors.index.json"
    shards = sorted(path.glob("*.safetensors"))
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            weight_map = index.get("weight_map", {})
            expected = {path / filename for filename in weight_map.values()}
            missing = sorted(str(item.name) for item in expected if not item.is_file())
            if missing:
                errors.append(f"missing safetensors shards: {', '.join(missing)}")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"invalid model.safetensors.index.json: {exc}")
    elif not shards:
        errors.append("missing safetensors weights or index")

    empty = [item.name for item in shards if item.stat().st_size == 0]
    if empty:
        errors.append(f"empty safetensors files: {', '.join(empty)}")
    return ValidationResult(not errors, tuple(errors), len(shards))
