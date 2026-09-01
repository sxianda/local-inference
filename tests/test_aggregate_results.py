from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path("benchmarks/aggregate_results.py").resolve()
SPEC = importlib.util.spec_from_file_location("aggregate_results", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_aggregate_exposes_failed_and_pending_gates() -> None:
    payload = MODULE.aggregate(Path("results"))
    assert len(payload["models"]) == 3
    assert payload["qwen38_tool_schema_success"]["total"] == 12
    assert payload["acceptance_gates"]["warm_ttft_speedup"]["passed"] is False
    assert payload["acceptance_gates"]["dflash2_decode_tps"]["observed"] is None
