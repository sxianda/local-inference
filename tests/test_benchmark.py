from local_inference.benchmark import BenchmarkResult


def test_benchmark_result_is_serializable_and_timestamped() -> None:
    result = BenchmarkResult(
        engine="rapid-mlx",
        engine_version="0.0.0",
        engine_commit="abc",
        model_id="dev-4b",
        model_name="default",
        quantization="MLX-4bit",
        scenario="smoke",
        prompt_tokens=10,
        completion_tokens=20,
        ttft_seconds=0.1,
        total_seconds=1.0,
        prompt_tps=100.0,
        decode_tps=20.0,
        cache_hit_tokens=0,
        peak_memory_gb=3.0,
    ).to_dict()
    assert result["created_at"]
    assert result["model_id"] == "dev-4b"

