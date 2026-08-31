from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class BenchmarkResult:
    engine: str
    engine_version: str
    engine_commit: str
    model_id: str
    model_name: str
    quantization: str
    scenario: str
    prompt_tokens: int
    completion_tokens: int
    ttft_seconds: float | None
    total_seconds: float
    prompt_tps: float | None
    decode_tps: float | None
    cache_hit_tokens: int | None
    peak_memory_gb: float | None
    tool_calls_valid: int | None = None
    tool_calls_total: int | None = None
    error: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload["created_at"]:
            payload["created_at"] = datetime.now(UTC).isoformat()
        return payload

