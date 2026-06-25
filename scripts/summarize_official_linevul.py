#!/usr/bin/env python
"""Summarize official LineVul checkpoint predictions with EaTVul gate flags."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score


ATTACK_LABELS = {
    "project_mimicry": "Project mimicry",
    "fragmented": "Fragmented insertion",
    "dead_branch": "Dead branch",
    "guarded_noop": "Guarded no-op",
}


def read_gate_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def gate_flags(rows: list[dict[str, object]]) -> list[int]:
    return [int(bool(row.get("gate_flag", 0))) for row in rows]


def load_preds(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "raw_preds" not in df.columns or "target" not in df.columns:
        raise ValueError(f"{path} must contain target and raw_preds columns")
    df["target"] = df["target"].astype(int)
    df["raw_preds"] = df["raw_preds"].astype(int)
    return df


def summarize_project(
    project: str,
    attack: str,
    prediction_dir: Path,
    gate_dir: Path,
) -> dict[str, object]:
    clean = load_preds(prediction_dir / f"{project}_clean_raw_preds.csv")
    adv = load_preds(prediction_dir / f"{project}_{attack}_raw_preds.csv")

    clean_gate_rows = read_gate_rows(gate_dir / f"{project}_tfidf_original_clean.jsonl")
    adv_gate_rows = read_gate_rows(gate_dir / f"{project}_tfidf_{attack}_adv.jsonl")
    clean_gate = gate_flags(clean_gate_rows)
    adv_gate = gate_flags(adv_gate_rows)
    if len(clean_gate) != len(clean):
        raise ValueError(f"Clean gate length mismatch for {project}: {len(clean_gate)} != {len(clean)}")
    if len(adv_gate) != len(adv):
        raise ValueError(f"Adv gate length mismatch for {project}/{attack}: {len(adv_gate)} != {len(adv)}")

    clean_pred = clean["raw_preds"].to_numpy().copy()
    clean_target = clean["target"].to_numpy()
    clean_defended = clean_pred.copy()
    clean_defended[[bool(x) for x in clean_gate]] = 1

    adv_pred = adv["raw_preds"].to_numpy()
    adv_target = adv["target"].to_numpy()
    if not all(x == 1 for x in adv_target):
        raise ValueError(f"Expected vulnerable-only attack file for {project}/{attack}")
    adv_bypass = adv_pred == 0
    adv_gate_bool = pd.Series(adv_gate).astype(bool).to_numpy()
    defended_bypass = adv_bypass & ~adv_gate_bool
    bypass_count = int(adv_bypass.sum())
    detected_bypass_count = int((adv_bypass & adv_gate_bool).sum())

    non_vul_mask = clean_target == 0
    clean_non_vul_fpr = (
        float(pd.Series(clean_gate)[non_vul_mask].mean()) if int(non_vul_mask.sum()) else 0.0
    )

    baseline_asr = float(adv_bypass.mean()) if len(adv_bypass) else 0.0
    defended_asr = float(defended_bypass.mean()) if len(defended_bypass) else 0.0

    return {
        "project": project,
        "victim": "official_linevul",
        "attack": attack,
        "attack_label": ATTACK_LABELS[attack],
        "clean_n": int(len(clean)),
        "adv_n": int(len(adv)),
        "validated_adv_n": int(
            sum(1 for row in adv_gate_rows if row.get("validation_status") == "compiler_valid")
        ),
        "clean_accuracy": float(accuracy_score(clean_target, clean_pred)),
        "clean_f1": float(f1_score(clean_target, clean_pred, zero_division=0)),
        "defended_clean_f1": float(f1_score(clean_target, clean_defended, zero_division=0)),
        "baseline_asr": baseline_asr,
        "defended_asr": defended_asr,
        "asr_reduction": baseline_asr - defended_asr,
        "adv_bypassed": bypass_count,
        "gate_detected_bypasses": detected_bypass_count,
        "gate_recall_on_bypassed": float(detected_bypass_count / bypass_count) if bypass_count else 0.0,
        "clean_non_vul_fpr": clean_non_vul_fpr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction-dir", type=Path, required=True)
    parser.add_argument("--gate-dir", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--projects", nargs="+", default=["linux", "ffmpeg"])
    parser.add_argument("--attacks", nargs="+", default=["project_mimicry", "fragmented"])
    args = parser.parse_args()

    rows = [
        summarize_project(project, attack, args.prediction_dir, args.gate_dir)
        for project in args.projects
        for attack in args.attacks
    ]
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
