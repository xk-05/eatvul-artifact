#!/usr/bin/env python3
"""Verify final manuscript Tables 2--9 against the released JISA evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "paper_eatvul_defense_framework" / "latex_submission" / "generated"
CONFIDENCE_DIR = ROOT / "results" / "jisa_confidence_sensitivity"
TARGETS = {"asterisk", "openssl", "cwe119", "cwe399"}
BUDGETS = np.asarray([0.01, 0.03, 0.05, 0.10, 0.15])

FINAL_TABLE_FRAGMENTS = {
    "Table 2": (
        "jisa_dataset_profile.tex",
        "20e19997b8088660206ce71be786c33a1e448cf036acc5354cff052cdaafa41e",
    ),
    "Table 3": (
        "jisa_matched_budget_5.tex",
        "6077325b98242f69d9d2793ec4de8363943f5f48d168d1ec080f1818e35b4298",
    ),
    "Table 4": (
        "jisa_confidence_baseline.tex",
        "4f6ed50cc2706b85f19e7657329d7a8c39739a2000c6bb339950a4c6ab79d865",
    ),
    "Table 5": (
        "jisa_duplicate_sensitivity.tex",
        "d06494f247b46eae43c08b38c6066df91928a1e13f769ddb0b968b10aeb52546",
    ),
    "Table 6": (
        "jisa_screening_stability.tex",
        "ba8f99560ab6842a0625d964f51d58d04d11f67a238dc2949ae487a1d041b8ad",
    ),
    "Table 7": (
        "jisa_codebert_results.tex",
        "36f47e54d80b3c97c7b666b7fc010bc1cd0b845409d267d3e73b782a0c5c0c89",
    ),
    "Table 8": (
        "jisa_token_length.tex",
        "5fb7a278eccadef0742680d2428f15545643fc143444008393117639e298624b",
    ),
    "Table 9": (
        "jisa_deletion_sensitivity.tex",
        "db2478893c65d25dd8480cdd51045e3ea5e7283b53c834b6e3e42d1d7cd2c60f",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_table_fragments() -> None:
    for table, (filename, expected_hash) in FINAL_TABLE_FRAGMENTS.items():
        path = GENERATED_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"{table}: missing generated fragment {path.relative_to(ROOT)}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise AssertionError(
                f"{table}: hash mismatch for {path.relative_to(ROOT)}; "
                f"expected={expected_hash}, actual={actual_hash}"
            )


def check_evidence_bundle() -> None:
    path = ROOT / "results" / "jisa_evidence_bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("verified") is not True:
        raise AssertionError("JISA evidence bundle is not marked verified")

    matched_runs = [
        run
        for experiment in bundle.get("experiments", [])
        if experiment.get("experiment") == "matched_budget_quarantine"
        for run in experiment.get("runs", [])
        if run.get("status") == "completed"
    ]
    if len(matched_runs) != 1:
        raise AssertionError(f"expected one completed matched-budget run, found {len(matched_runs)}")
    rows = matched_runs[0].get("summary", [])
    if len(rows) != 100:
        raise AssertionError(f"matched-budget evidence must contain 100 rows, found {len(rows)}")
    if {str(row["target"]).lower() for row in rows} != TARGETS:
        raise AssertionError("matched-budget evidence does not contain all four targets")

    materialized = pd.read_csv(ROOT / "results" / "jisa_matched_budget_summary.csv")
    if len(materialized) != 100 or set(materialized["target"].str.lower()) != TARGETS:
        raise AssertionError("materialized matched-budget summary is incomplete")


def check_confidence_outputs() -> None:
    summary = pd.read_csv(CONFIDENCE_DIR / "confidence_summary.csv")
    samples = pd.read_csv(CONFIDENCE_DIR / "confidence_adv_samples.csv")
    duplicates = pd.read_csv(CONFIDENCE_DIR / "duplicate_sensitivity.csv")
    profiles = pd.read_csv(CONFIDENCE_DIR / "token_length_profile.csv")

    if len(summary) != 20 or set(summary["dataset"].str.lower()) != TARGETS:
        raise AssertionError("confidence summary does not contain the 4-target x 5-budget grid")
    observed_budgets = np.sort(summary["budget"].unique())
    if not np.allclose(observed_budgets, BUDGETS):
        raise AssertionError(f"unexpected confidence budgets: {observed_budgets.tolist()}")
    if len(samples) != 2500:
        raise AssertionError(f"confidence sample output must contain 2500 rows, found {len(samples)}")
    if len(duplicates) != 15:
        raise AssertionError(f"duplicate sensitivity must contain 15 rows, found {len(duplicates)}")
    if len(profiles) != 12:
        raise AssertionError(f"token profile must contain 12 rows, found {len(profiles)}")


def main() -> int:
    check_table_fragments()
    check_evidence_bundle()
    check_confidence_outputs()
    print("Reported-value check passed: final Tables 2-9 match the verified JISA evidence.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
