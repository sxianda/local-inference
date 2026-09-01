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
model = "agent-9b"
model_provider = "rapid-mlx"
model_reasoning_effort = "none"

[features]
apps = false
browser_use = false
computer_use = false
goals = false
image_generation = false
in_app_browser = false
multi_agent = false
plugins = false
recommended_plugins = false
remote_plugin = false
skill_search = false
tool_suggest = false
view_image = false
workspace_dependencies = false
"""
SKIP_HOST_PROFILE_CONTENT = PROFILE_CONTENT.replace(
    "tool_suggest = false", "skip_host_skill_discovery = true\ntool_suggest = false"
)
LEGACY_PROFILE_CONTENT = """# Local Rapid-MLX overlay; use with: codex --profile rapid-mlx
model = "agent-9b"
model_provider = "rapid-mlx"
model_supports_reasoning_summaries = false
"""
PREVIOUS_PROFILE_CONTENT = """# Local Rapid-MLX overlay; use with: codex --profile rapid-mlx
model = "agent-9b"
model_provider = "rapid-mlx"
"""
LOW_REASONING_PROFILE_CONTENT = """# Local Rapid-MLX overlay; use with: codex --profile rapid-mlx
model = "agent-9b"
model_provider = "rapid-mlx"
model_reasoning_effort = "low"
"""
NONE_REASONING_PROFILE_CONTENT = """# Local Rapid-MLX overlay; use with: codex --profile rapid-mlx
model = "agent-9b"
model_provider = "rapid-mlx"
model_reasoning_effort = "none"
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
    if profile_path.exists():
        existing_profile = profile_path.read_text(encoding="utf-8")
        if existing_profile not in {
            PROFILE_CONTENT,
            LEGACY_PROFILE_CONTENT,
            PREVIOUS_PROFILE_CONTENT,
            LOW_REASONING_PROFILE_CONTENT,
            NONE_REASONING_PROFILE_CONTENT,
            SKIP_HOST_PROFILE_CONTENT,
        }:
            raise SystemExit(f"existing {profile_path} differs; refusing to overwrite")
    profile_path.write_text(PROFILE_CONTENT, encoding="utf-8")
    print(f"Configured provider in {config_path}")
    print(f"Configured profile in {profile_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
