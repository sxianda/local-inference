from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("config/models.local.yaml")
FALLBACK_CONFIG = Path("config/models.example.yaml")


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    path: Path
    role: str
    quantization: str
    modelscope: str | None = None
    huggingface: str | None = None
    extra_args: tuple[str, ...] = ()
    requires_tokenizer: bool = True


def _expand(value: str) -> str:
    return os.path.expandvars(os.path.expanduser(value))


def resolve_config_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    return FALLBACK_CONFIG


def load_registry(path: str | Path | None = None) -> dict[str, ModelSpec]:
    config_path = resolve_config_path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        payload: dict[str, Any] = yaml.safe_load(handle) or {}

    raw_models = payload.get("models")
    if not isinstance(raw_models, dict) or not raw_models:
        raise ValueError(f"{config_path} must contain a non-empty 'models' mapping")

    registry: dict[str, ModelSpec] = {}
    for model_id, raw in raw_models.items():
        if not isinstance(raw, dict):
            raise ValueError(f"model {model_id!r} must be a mapping")
        raw_path = raw.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError(f"model {model_id!r} requires a path")
        extra_args = raw.get("extra_args", [])
        if not isinstance(extra_args, list) or not all(isinstance(x, str) for x in extra_args):
            raise ValueError(f"model {model_id!r} extra_args must be a list of strings")
        registry[model_id] = ModelSpec(
            model_id=model_id,
            path=Path(_expand(raw_path)),
            role=str(raw.get("role", "unspecified")),
            quantization=str(raw.get("quantization", "unknown")),
            modelscope=raw.get("modelscope"),
            huggingface=raw.get("huggingface"),
            extra_args=tuple(extra_args),
            requires_tokenizer=bool(raw.get("requires_tokenizer", True)),
        )
    return registry


def get_model(model_id: str, path: str | Path | None = None) -> ModelSpec:
    registry = load_registry(path)
    try:
        return registry[model_id]
    except KeyError as exc:
        choices = ", ".join(sorted(registry))
        raise KeyError(f"unknown model {model_id!r}; choose one of: {choices}") from exc
