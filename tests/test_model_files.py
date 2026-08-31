import json
from pathlib import Path

from local_inference.model_files import validate_model_directory


def test_valid_single_file_model(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    result = validate_model_directory(tmp_path)
    assert result.valid


def test_index_requires_all_shards(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    index = {
        "weight_map": {
            "a": "model-00001-of-00002.safetensors",
            "b": "model-00002-of-00002.safetensors",
        }
    }
    (tmp_path / "model.safetensors.index.json").write_text(json.dumps(index), encoding="utf-8")
    (tmp_path / "model-00001-of-00002.safetensors").write_bytes(b"weights")
    result = validate_model_directory(tmp_path)
    assert not result.valid
    assert "model-00002-of-00002.safetensors" in " ".join(result.errors)


def test_drafter_can_reuse_target_tokenizer(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    result = validate_model_directory(tmp_path, require_tokenizer=False)
    assert result.valid
