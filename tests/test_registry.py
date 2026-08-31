from pathlib import Path

import pytest

from local_inference.registry import get_model, load_registry


def test_example_registry_contains_required_models() -> None:
    registry = load_registry(Path("config/models.example.yaml"))
    assert set(registry) == {
        "dev-4b",
        "agent-9b",
        "qwen38-27b",
        "qwen38-dflash2-q4",
        "qwen38-dflash2-bf16",
    }
    assert all(spec.path.is_absolute() for spec in registry.values())
    assert all(str(spec.path).startswith("/Users/soleilx/Models/") for spec in registry.values())


def test_unknown_model_has_actionable_message() -> None:
    with pytest.raises(KeyError, match="choose one of"):
        get_model("missing", Path("config/models.example.yaml"))

