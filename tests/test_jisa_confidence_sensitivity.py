from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jisa_confidence_sensitivity import (  # noqa: E402
    OUT_DIR,
    apply_tie_policy,
    calibrate_tie_policy,
    content_hash,
    verify_outputs,
)


def test_tie_policy_hits_requested_calibration_count() -> None:
    scores = np.array([0.9, 0.8, 0.8, 0.8, 0.1])
    ids = [f"sample-{index}" for index in range(len(scores))]
    policy = calibrate_tie_policy(scores, ids, budget=0.4)
    reviewed = apply_tie_policy(scores, ids, policy)
    assert reviewed.sum() == 2
    assert policy.inclusive_count == 4
    assert policy.target_count == 2
    assert policy.tie_count == 3


def test_content_hash_ignores_whitespace_only_changes() -> None:
    assert content_hash("A  B\nC") == content_hash(" A B C ")
    assert content_hash("A B C") != content_hash("A B D")


def test_generated_outputs_recompute_from_sample_rows() -> None:
    verify_outputs(OUT_DIR)
