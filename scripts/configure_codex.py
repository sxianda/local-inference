#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import tomllib
from datetime import UTC, datetime
from pathlib import Path

PROVIDER_ID = "rapid-mlx"
PROVIDER_BLOCK = """

[model_providers.rapid-mlx]
name = "Rapid-MLX Local"
base_url = "http://127.0.0.1:8000/v1"
wire_api = "responses"
requires_openai_auth = false
stream_idle_timeout_ms = 600000
"""
PROFILE_CONTENT = """# Local Rapid-MLX overlay; use with: codex --profile rapid-mlx
model = "default"
model_provider = "rapid-mlx"
model_supports_reasoning_summaries = false
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely configure Codex for local Rapid-MLX")
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.codex_dir / "config.toml"
    profile_path = args.codex_dir / "rapid-mlx.config.toml"
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    parsed = tomllib.loads(original) if original.strip() else {}
    providers = parsed.get("model_providers", {})
    existing = providers.get(PROVIDER_ID)
    expected = {
        "name": "Rapid-MLX Local",
        "base_url": "http://127.0.0.1:8000/v1",
        "wire_api": "responses",
        "requires_openai_auth": False,
        "stream_idle_timeout_ms": 600000,
    }
    if existing is not None and existing != expected:
        raise SystemExit("existing model_providers.rapid-mlx differs; refusing to overwrite")

    updated = original if existing == expected else original.rstrip() + PROVIDER_BLOCK
    tomllib.loads(updated)
    tomllib.loads(PROFILE_CONTENT)
    if args.dry_run:
        print(f"Would update {config_path} and {profile_path}")
        return 0

    args.codex_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if config_path.exists() and updated != original:
        backup = args.codex_dir / f"config.toml.before-rapid-mlx.{stamp}"
        shutil.copy2(config_path, backup)
        print(f"Backup: {backup}")
    if updated != original:
        config_path.write_text(updated, encoding="utf-8")
    if profile_path.exists() and profile_path.read_text(encoding="utf-8") != PROFILE_CONTENT:
        raise SystemExit(f"existing {profile_path} differs; refusing to overwrite")
    profile_path.write_text(PROFILE_CONTENT, encoding="utf-8")
    print(f"Configured provider in {config_path}")
    print(f"Configured profile in {profile_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

