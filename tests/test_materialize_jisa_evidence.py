from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import materialize_jisa_evidence as materialize  # noqa: E402
from materialize_jisa_evidence import load_bundle, matched_summary  # noqa: E402


def test_verified_bundle_contains_complete_matched_budget_grid() -> None:
    bundle = load_bundle(ROOT / "results" / "jisa_evidence_bundle.json")
    rows = matched_summary(bundle)
    assert bundle["verified"] is True
    assert len(rows) == 100
    assert {row["target"] for row in rows} == {"asterisk", "openssl", "cwe119", "cwe399"}


def test_dataset_profile_materializes_without_raw_splits(tmp_path, monkeypatch) -> None:
    profile = tmp_path / "results" / "jisa_confidence_sensitivity" / "token_length_profile.csv"
    profile.parent.mkdir(parents=True)
    source_profile = ROOT / "results" / "jisa_confidence_sensitivity" / "token_length_profile.csv"
    profile.write_bytes(source_profile.read_bytes())
    generated = tmp_path / "generated"
    generated.mkdir()

    monkeypatch.setattr(materialize, "ROOT", tmp_path)
    monkeypatch.setattr(materialize, "GEN_DIR", generated)

    materialize.make_dataset_profile()

    output = (generated / "jisa_dataset_profile.tex").read_text(encoding="utf-8")
    assert "ASTERISK & 880 & 367 & 50 & 4277 & 3893 & 4697" in output
    assert "CWE399 & 545 & 255 & 200 & 2547 & 2356 & 2192" in output
