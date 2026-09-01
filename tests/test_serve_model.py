from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/serve_model.py").resolve()


def test_launcher_rejects_an_occupied_port_before_model_load() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "dev-4b", "--port", str(port)],
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode != 0
    assert f"127.0.0.1:{port} already has a listener" in result.stderr
