from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

BASE_URL = os.getenv("RAPID_MLX_BASE_URL")
MODEL = os.getenv("RAPID_MLX_MODEL", "default")
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
        assert MODEL in {item["id"] for item in models.json()["data"]}
        response = client.post(
            f"{base_url}/responses",
            json={"model": MODEL, "input": "Reply exactly: RESPONSES_OK", "stream": False},
        )
        assert response.status_code == 200
        assert response.json().get("object") == "response"


def test_chat_completion_and_stream() -> None:
    base_url = require_server()
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply exactly: CHAT_OK"}],
        "max_tokens": 32,
    }
    with httpx.Client(timeout=600) as client:
        response = client.post(f"{base_url}/chat/completions", json=payload)
        assert response.status_code == 200
        assert response.json()["object"] == "chat.completion"
        with client.stream(
            "POST", f"{base_url}/chat/completions", json={**payload, "stream": True}
        ) as stream:
            assert stream.status_code == 200
            lines = [line for line in stream.iter_lines() if line]
    assert lines[-1] == "data: [DONE]"


def test_responses_sse_completes() -> None:
    base_url = require_server()
    event_types: list[str] = []
    with httpx.Client(timeout=600) as client, client.stream(
        "POST",
        f"{base_url}/responses",
        json={"model": MODEL, "input": "Reply exactly: STREAM_OK", "stream": True},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_types.append(line.removeprefix("event:").strip())
    assert event_types[0] == "response.created"
    assert "response.output_text.delta" in event_types
    assert event_types[-1] == "response.completed"


def test_invalid_request_is_structured() -> None:
    base_url = require_server()
    response = httpx.post(f"{base_url}/responses", json={"model": MODEL}, timeout=30)
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"


def test_concurrent_requests_complete() -> None:
    base_url = require_server()

    def request(index: int) -> int:
        response = httpx.post(
            f"{base_url}/responses",
            json={"model": MODEL, "input": f"Reply exactly: CONCURRENT_{index}"},
            timeout=600,
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(request, range(2))) == [200, 200]


def test_client_cancellation_and_timeout_leave_server_healthy() -> None:
    base_url = require_server()
    payload = {
        "model": MODEL,
        "input": "Write the word token two hundred times.",
        "stream": True,
        "max_output_tokens": 512,
    }
    with httpx.Client(timeout=600) as client, client.stream(
        "POST", f"{base_url}/responses", json=payload
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("event: response.output_text.delta"):
                break

    with pytest.raises(httpx.TimeoutException):
        httpx.post(
            f"{base_url}/responses",
            json={**payload, "stream": False},
            timeout=httpx.Timeout(0.001),
        )

    assert httpx.get(f"{base_url}/models", timeout=30).status_code == 200
