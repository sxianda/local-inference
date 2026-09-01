from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPT = Path("scripts/configure_codex.py").resolve()


def test_configurator_preserves_default_and_is_idempotent(tmp_path: Path) -> None:
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    config = codex_dir / "config.toml"
    config.write_text('model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n', encoding="utf-8")

    command = [sys.executable, str(SCRIPT), "--codex-dir", str(codex_dir)]
    subprocess.run(command, check=True)
    first = config.read_text(encoding="utf-8")
    subprocess.run(command, check=True)
    second = config.read_text(encoding="utf-8")

    parsed = tomllib.loads(second)
    assert first == second
    assert parsed["model"] == "gpt-5.6-sol"
    assert parsed["model_providers"]["rapid-mlx"]["wire_api"] == "responses"
    profile = tomllib.loads((codex_dir / "rapid-mlx.config.toml").read_text(encoding="utf-8"))
    assert profile["model"] == "agent-9b"
    assert profile["model_provider"] == "rapid-mlx"
    assert profile["model_reasoning_effort"] == "none"
    assert profile["features"]["plugins"] is False
    assert profile["features"]["apps"] is False
    assert list(codex_dir.glob("config.toml.before-rapid-mlx.*"))
