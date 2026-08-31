from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv("RAPID_MLX_BASE_URL")
pytestmark = pytest.mark.model


def require_server() -> str:
    if not BASE_URL:
        pytest.skip("set RAPID_MLX_BASE_URL to run model-backed API tests")
    return BASE_URL.rstrip("/")


def test_models_and_responses() -> None:
    base_url = require_server()
    with httpx.Client(timeout=600) as client:
        models = client.get(f"{base_url}/models")
        assert models.status_code == 200
        response = client.post(
            f"{base_url}/responses",
            json={"model": "default", "input": "Reply exactly: RESPONSES_OK", "stream": False},
        )
        assert response.status_code == 200
        assert response.json().get("object") == "response"


def test_responses_sse_completes() -> None:
    base_url = require_server()
    event_types: list[str] = []
    with httpx.Client(timeout=600) as client, client.stream(
        "POST",
        f"{base_url}/responses",
        json={"model": "default", "input": "Reply exactly: STREAM_OK", "stream": True},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_types.append(line.removeprefix("event:").strip())
    assert "response.created" in event_types
    assert "response.completed" in event_types

