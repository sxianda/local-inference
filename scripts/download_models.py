#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from local_inference.model_files import validate_model_directory
from local_inference.registry import ModelSpec, load_registry


def find_environment_command(name: str) -> str:
    candidate = Path(sys.executable).parent / name
    if candidate.is_file():
        return str(candidate)
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} CLI is not installed")
    return executable


def run_download(source: str, repo_id: str, destination: Path, dry_run: bool) -> None:
    if source == "modelscope":
        print(f"modelscope: {repo_id} -> {destination}")
        if dry_run:
            return
        from modelscope import snapshot_download

        snapshot_download(repo_id, local_dir=str(destination))
        return
    executable = find_environment_command("hf")
    command = [executable, "download", repo_id, "--local-dir", str(destination)]
    print(f"huggingface: {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def download_model(spec: ModelSpec, dry_run: bool = False) -> None:
    current = validate_model_directory(spec.path, require_tokenizer=spec.requires_tokenizer)
    if current.valid:
        print(f"skip {spec.model_id}: already valid at {spec.path}")
        return
    if spec.path.exists():
        detail = "; ".join(current.errors)
        raise RuntimeError(f"refusing to overwrite invalid existing path {spec.path}: {detail}")

    sources = [
        ("modelscope", spec.modelscope),
        ("huggingface", spec.huggingface),
    ]
    sources = [(name, repo) for name, repo in sources if repo]
    if not sources:
        raise RuntimeError(f"{spec.model_id} has no configured download source")

    staging_root = spec.path.parent / ".downloads"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    errors: list[str] = []
    for source, repo_id in sources:
        stage = staging_root / f"{spec.path.name}.{source}.{stamp}.partial"
        try:
            if dry_run:
                run_download(source, repo_id, stage, dry_run=True)
                return
            stage.mkdir(parents=True, exist_ok=False)
            run_download(source, repo_id, stage, dry_run=False)
            result = validate_model_directory(stage, require_tokenizer=spec.requires_tokenizer)
            if not result.valid:
                raise RuntimeError("; ".join(result.errors))
            stage.replace(spec.path)
            print(f"ready {spec.model_id}: {spec.path}")
            return
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            errors.append(f"{source}: {exc}")
            print(f"warning: {errors[-1]}", file=sys.stderr)
    message = "all download sources failed; partial directories were retained: "
    raise RuntimeError(message + " | ".join(errors))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download registered MLX models safely")
    parser.add_argument(
        "model_ids", nargs="*", help="model IDs; defaults to downloadable dev models"
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--all", action="store_true", help="download every model with a source")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_registry(args.config)
    if args.all:
        selected = [spec for spec in registry.values() if spec.modelscope or spec.huggingface]
    else:
        model_ids = args.model_ids or ["dev-4b", "agent-9b"]
        unknown = sorted(set(model_ids) - registry.keys())
        if unknown:
            raise SystemExit(f"unknown model IDs: {', '.join(unknown)}")
        selected = [registry[model_id] for model_id in model_ids]
    for spec in selected:
        download_model(spec, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
