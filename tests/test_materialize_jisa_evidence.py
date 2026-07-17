from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_jisa_evidence import load_bundle, matched_summary  # noqa: E402


def test_verified_bundle_contains_complete_matched_budget_grid() -> None:
    bundle = load_bundle(ROOT / "results" / "jisa_evidence_bundle.json")
    rows = matched_summary(bundle)
    assert bundle["verified"] is True
    assert len(rows) == 100
    assert {row["target"] for row in rows} == {"asterisk", "openssl", "cwe119", "cwe399"}
