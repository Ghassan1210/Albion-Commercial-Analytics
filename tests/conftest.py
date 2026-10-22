"""Keep acquisition-mode tests from leaving the shared provenance manifest changed."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "04_reconciliation" / "provenance_manifest.json"


@pytest.fixture(autouse=True)
def restore_provenance_manifest():
    """Restore the manifest after tests that exercise fixture/full acquisition."""
    existed = MANIFEST.exists()
    original = MANIFEST.read_text(encoding="utf-8") if existed else None
    yield
    if existed and original is not None:
        MANIFEST.write_text(original, encoding="utf-8")
    elif not existed and MANIFEST.exists():
        MANIFEST.unlink()
