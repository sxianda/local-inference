# Disposable Codex fixture

This fixture intentionally contains one failing test. Copy it to a temporary directory before an
Agent evaluation; never ask Codex to modify the committed fixture in place.

Suggested sequence: explain the files, run pytest, repair the bug, add one edge-case test, rename a
function across both files, and rerun pytest.

