from pathlib import Path


def test_agent_fixture_uses_local_codex_patch_contract() -> None:
    script = Path("scripts/run_codex_fixture.sh").read_text(encoding="utf-8")
    assert "apply_patch <<'PATCH'" in script
    assert "*** Begin Patch" in script
    assert "*** Update File: calculator.py" in script
    assert "The hunk marker must be only @@" in script
    assert "do not use sed" in script
