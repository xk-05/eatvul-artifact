#!/usr/bin/env python3
"""Target-confidence, tie-aware calibration, and duplicate sensitivity checks.

This experiment is deliberately independent of attack-labelled detector fitting:
each target model is fitted only on a stratified detector-training portion of its
own official training split.  The held-out training portion calibrates review
thresholds.  Official clean and adversarial test rows are queried once.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Code and Dataset" / "file" / "data"
OUT_DIR = ROOT / "results" / "jisa_confidence_sensitivity"
DATASETS = ("asterisk", "openssl", "cwe119", "cwe399")
BUDGETS = (0.01, 0.03, 0.05, 0.10, 0.15)
SEED = 7


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalized_text(text).encode("utf-8")).hexdigest()


def _hash_uniform(identifier: str) -> float:
    value = int.from_bytes(hashlib.sha256(identifier.encode("utf-8")).digest()[:8], "big")
    return value / float(2**64)


@dataclass(frozen=True)
class TiePolicy:
    threshold: float
    tie_hash_cutoff: float
    target_count: int
    inclusive_count: int
    above_count: int
    tie_count: int
    calibration_size: int
    nominal_budget: float


def calibrate_tie_policy(scores: np.ndarray, ids: Sequence[str], budget: float) -> TiePolicy:
    scores = np.asarray(scores, dtype=float)
    if len(scores) != len(ids) or len(scores) == 0:
        raise ValueError("scores and ids must be non-empty and aligned")
    if not 0.0 < budget < 1.0 or not np.isfinite(scores).all():
        raise ValueError("budget and scores must be finite")
    target = min(len(scores), max(1, int(math.ceil(budget * len(scores)))))
    threshold = float(np.sort(scores)[-target])
    above = scores > threshold
    tied = scores == threshold
    needed = target - int(above.sum())
    tie_hashes = sorted(_hash_uniform(ids[index]) for index in np.flatnonzero(tied))
    cutoff = tie_hashes[needed - 1] if needed else -1.0
    return TiePolicy(
        threshold=threshold,
        tie_hash_cutoff=float(cutoff),
        target_count=target,
        inclusive_count=int((scores >= threshold).sum()),
        above_count=int(above.sum()),
        tie_count=int(tied.sum()),
        calibration_size=len(scores),
        nominal_budget=float(budget),
    )


def apply_tie_policy(scores: np.ndarray, ids: Sequence[str], policy: TiePolicy) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    if len(scores) != len(ids):
        raise ValueError("scores and ids must be aligned")
    above = scores > policy.threshold
    tied = scores == policy.threshold
    tie_selected = np.fromiter(
        (_hash_uniform(identifier) <= policy.tie_hash_cutoff for identifier in ids),
        dtype=bool,
        count=len(ids),
    )
    return above | (tied & tie_selected)


def load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def make_ids(dataset: str, split: str, items: Sequence[dict[str, object]]) -> list[str]:
    return [f"{dataset}:{split}:{index}:{content_hash(str(item['func']))[:16]}" for index, item in enumerate(items)]


def texts_labels(items: Sequence[dict[str, object]]) -> tuple[list[str], np.ndarray]:
    return [str(item["func"]) for item in items], np.asarray([int(item["target"]) for item in items])


def train_target(texts: Sequence[str], labels: np.ndarray) -> Pipeline:
    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    tokenizer=str.split,
                    preprocessor=None,
                    token_pattern=None,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=50_000,
                    sublinear_tf=True,
                    dtype=np.float32,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED)),
        ]
    )
    model.fit(texts, labels)
    return model


def token_profile(dataset: str, split: str, items: Sequence[dict[str, object]]) -> dict[str, object]:
    lengths = np.asarray([len(str(item["func"]).split()) for item in items], dtype=int)
    return {
        "dataset": dataset,
        "split": split,
        "n": len(lengths),
        "median_tokens": float(np.median(lengths)),
        "p95_tokens": float(np.percentile(lengths, 95)),
        "fraction_over_256": float(np.mean(lengths > 256)),
        "fraction_over_512": float(np.mean(lengths > 512)),
    }


def evaluate_target(dataset: str) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    train_items = load_jsonl(DATA_DIR / f"{dataset}_ast_train.json")
    test_items = load_jsonl(DATA_DIR / f"{dataset}_ast_test.json")
    adv_items = load_jsonl(DATA_DIR / f"{dataset}_ast_test_ADV.json")
    train_texts, train_labels = texts_labels(train_items)
    fit_idx, cal_idx = train_test_split(
        np.arange(len(train_items)), test_size=0.20, random_state=SEED, stratify=train_labels
    )
    model = train_target([train_texts[index] for index in fit_idx], train_labels[fit_idx])

    cal_texts = [train_texts[index] for index in cal_idx]
    cal_labels = train_labels[cal_idx]
    test_texts, test_labels = texts_labels(test_items)
    adv_texts, adv_labels = texts_labels(adv_items)
    cal_prob = model.predict_proba(cal_texts)[:, 1]
    test_prob = model.predict_proba(test_texts)[:, 1]
    adv_prob = model.predict_proba(adv_texts)[:, 1]
    cal_pred = (cal_prob >= 0.5).astype(int)
    test_pred = (test_prob >= 0.5).astype(int)
    adv_pred = (adv_prob >= 0.5).astype(int)

    cal_ids_all = [f"{dataset}:cal:{int(index)}:{content_hash(train_texts[index])[:16]}" for index in cal_idx]
    test_ids = make_ids(dataset, "test", test_items)
    adv_ids = make_ids(dataset, "adv", adv_items)
    cal_eligible = (cal_labels == 0) & (cal_pred == 0)
    test_true_benign_eligible = (test_labels == 0) & (test_pred == 0)
    if not cal_eligible.any():
        raise RuntimeError(f"{dataset}: no true-benign predicted-benign calibration rows")

    rows: list[dict[str, object]] = []
    samples: list[dict[str, object]] = []
    base_f1 = f1_score(test_labels, test_pred, zero_division=0)
    for budget in BUDGETS:
        policy = calibrate_tie_policy(
            cal_prob[cal_eligible],
            [identifier for identifier, keep in zip(cal_ids_all, cal_eligible) if keep],
            budget,
        )
        cal_selected = apply_tie_policy(
            cal_prob[cal_eligible],
            [identifier for identifier, keep in zip(cal_ids_all, cal_eligible) if keep],
            policy,
        )
        test_selected_all = apply_tie_policy(test_prob, test_ids, policy) & (test_pred == 0)
        test_selected_budget = test_selected_all & test_true_benign_eligible
        adv_selected = apply_tie_policy(adv_prob, adv_ids, policy) & (adv_pred == 0)
        cal_exact_rate = float(cal_selected.mean())
        cal_inclusive_rate = policy.inclusive_count / policy.calibration_size
        test_transfer_rate = float(test_selected_budget.sum() / max(1, test_true_benign_eligible.sum()))
        rows.append(
            {
                "dataset": dataset,
                "budget": budget,
                "calibration_n": policy.calibration_size,
                "target_count": policy.target_count,
                "threshold": policy.threshold,
                "tie_count": policy.tie_count,
                "inclusive_count": policy.inclusive_count,
                "calibration_exact_rate": cal_exact_rate,
                "calibration_inclusive_rate": cal_inclusive_rate,
                "rounding_gap": cal_exact_rate - budget,
                "tie_overshoot": cal_inclusive_rate - cal_exact_rate,
                "test_true_benign_review_rate": test_transfer_rate,
                "calibration_to_test_drift": test_transfer_rate - cal_exact_rate,
                "test_review_count": int(test_selected_all.sum()),
                "test_review_rate": float(test_selected_all.mean()),
                "test_predicted_benign": int((test_pred == 0).sum()),
                "baseline_clean_f1": float(base_f1),
                "adv_n": len(adv_items),
                "adv_benign_predictions": int((adv_pred == 0).sum()),
                "adv_captured": int(adv_selected.sum()),
                "adv_capture_rate": float(adv_selected.mean()),
                "residual_silent_bypass_rate": float(((adv_pred == 0) & ~adv_selected).mean()),
            }
        )
        for index in range(len(adv_items)):
            samples.append(
                {
                    "dataset": dataset,
                    "budget": budget,
                    "sample_id": adv_ids[index],
                    "content_hash": content_hash(adv_texts[index]),
                    "vulnerable_probability": float(adv_prob[index]),
                    "baseline_benign": int(adv_pred[index] == 0),
                    "captured": int(adv_selected[index]),
                }
            )
    profiles = [
        token_profile(dataset, "train", train_items),
        token_profile(dataset, "test", test_items),
        token_profile(dataset, "adv", adv_items),
    ]
    return rows, samples, profiles


def duplicate_sensitivity(samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for budget, part in samples.groupby("budget"):
        for order_name, order in (("forward", list(DATASETS)), ("reverse", list(reversed(DATASETS)))):
            ranked = part.assign(_rank=part["dataset"].map({name: i for i, name in enumerate(order)}))
            unique = ranked.sort_values(["_rank", "sample_id"]).drop_duplicates("content_hash", keep="first")
            for label, frame in (("all_rows", part), (f"deduplicated_{order_name}", unique)):
                benign = int(frame["baseline_benign"].sum())
                captured = int(frame["captured"].sum())
                rows.append(
                    {
                        "budget": budget,
                        "analysis": label,
                        "rows": len(frame),
                        "unique_content_hashes": frame["content_hash"].nunique(),
                        "baseline_benign": benign,
                        "captured": captured,
                        "capture_among_all": captured / len(frame),
                        "capture_among_bypasses": captured / benign if benign else float("nan"),
                    }
                )
    return pd.DataFrame(rows).drop_duplicates(["budget", "analysis"])


def write_tex(summary: pd.DataFrame, profiles: pd.DataFrame, duplicates: pd.DataFrame) -> None:
    generated = ROOT / "paper_eatvul_defense_framework" / "latex_submission" / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    five = summary[np.isclose(summary["budget"], 0.05)]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Target-confidence baseline at a 5\\% nominal calibration budget. Review and capture are evaluated on untouched test roles.}",
        "\\label{tab:confidence-baseline}",
        "\\scriptsize",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Target & Cal. $n$ & Tie over. & Drift & Review & Captured & Residual \\\\",
        "\\midrule",
    ]
    for row in five.itertuples(index=False):
        lines.append(
            f"{str(row.dataset).upper()} & {row.calibration_n} & {100*row.tie_overshoot:.1f} pp & "
            f"{100*row.calibration_to_test_drift:.1f} pp & {100*row.test_review_rate:.1f}\\% & "
            f"{row.adv_captured}/{row.adv_benign_predictions} & {100*row.residual_silent_bypass_rate:.1f}\\% \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (generated / "jisa_confidence_baseline.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    prof = profiles[profiles["split"].isin(["test", "adv"])]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Serialized AST-token length relative to the 256-token CodeBERT limit.}",
        "\\label{tab:length-truncation}",
        "\\scriptsize",
        "\\begin{tabular}{llrrr}",
        "\\toprule",
        "Target & Role & Median & P95 & $>256$ \\\\",
        "\\midrule",
    ]
    for row in prof.itertuples(index=False):
        lines.append(
            f"{str(row.dataset).upper()} & {row.split} & {row.median_tokens:.0f} & {row.p95_tokens:.0f} & "
            f"{100*row.fraction_over_256:.1f}\\% \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (generated / "jisa_token_length.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dup5 = duplicates[np.isclose(duplicates["budget"], 0.05)]
    (generated / "jisa_duplicate_sensitivity.tex").write_text(
        "\\begin{table}[t]\n\\centering\n"
        "\\caption{Micro-average duplicate sensitivity for the confidence baseline at 5\\%.}\n"
        "\\label{tab:duplicate-sensitivity}\n\\scriptsize\n"
        "\\begin{tabular}{lrrrr}\n\\toprule\nAnalysis & Rows & Unique & Captured & Capture/bypass \\\\\n\\midrule\n"
        + "\n".join(
            f"{row.analysis.replace('_', ' ')} & {row.rows} & {row.unique_content_hashes} & {row.captured} & "
            f"{100*row.capture_among_bypasses:.1f}\\% \\\\"
            for row in dup5.itertuples(index=False)
        )
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n",
        encoding="utf-8",
    )


def verify_outputs(output_dir: Path) -> None:
    summary = pd.read_csv(output_dir / "confidence_summary.csv")
    samples = pd.read_csv(output_dir / "confidence_adv_samples.csv")
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if set(summary["dataset"]) != set(DATASETS) or len(summary) != len(DATASETS) * len(BUDGETS):
        raise AssertionError("summary does not contain the complete target-budget grid")
    for name, metadata in manifest["outputs"].items():
        observed = hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        if observed != metadata["sha256"]:
            raise AssertionError(f"hash mismatch: {name}")
    for row in summary.itertuples(index=False):
        part = samples[(samples["dataset"] == row.dataset) & np.isclose(samples["budget"], row.budget)]
        if len(part) != row.adv_n:
            raise AssertionError(f"adversarial row count mismatch: {row.dataset}/{row.budget}")
        if int(part["baseline_benign"].sum()) != row.adv_benign_predictions:
            raise AssertionError(f"bypass count mismatch: {row.dataset}/{row.budget}")
        if int(part["captured"].sum()) != row.adv_captured:
            raise AssertionError(f"capture count mismatch: {row.dataset}/{row.budget}")
        expected_residual = (row.adv_benign_predictions - row.adv_captured) / row.adv_n
        if not np.isclose(expected_residual, row.residual_silent_bypass_rate):
            raise AssertionError(f"residual mismatch: {row.dataset}/{row.budget}")


def run() -> None:
    start = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    all_samples: list[dict[str, object]] = []
    all_profiles: list[dict[str, object]] = []
    for dataset in DATASETS:
        rows, samples, profiles = evaluate_target(dataset)
        all_rows.extend(rows)
        all_samples.extend(samples)
        all_profiles.extend(profiles)
        print(f"completed {dataset}", flush=True)
    summary = pd.DataFrame(all_rows)
    samples = pd.DataFrame(all_samples)
    profiles = pd.DataFrame(all_profiles)
    duplicates = duplicate_sensitivity(samples)
    summary.to_csv(OUT_DIR / "confidence_summary.csv", index=False)
    samples.to_csv(OUT_DIR / "confidence_adv_samples.csv", index=False)
    profiles.to_csv(OUT_DIR / "token_length_profile.csv", index=False)
    duplicates.to_csv(OUT_DIR / "duplicate_sensitivity.csv", index=False)
    write_tex(summary, profiles, duplicates)
    manifest = {
        "experiment": "jisa-confidence-tie-duplicate-sensitivity",
        "seed": SEED,
        "budgets": BUDGETS,
        "datasets": DATASETS,
        "runtime_seconds": time.time() - start,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {"numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "outputs": {},
    }
    for path in sorted(OUT_DIR.glob("*.csv")):
        manifest["outputs"][path.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
    (OUT_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    verify_outputs(OUT_DIR)
    print(f"wrote {OUT_DIR} in {manifest['runtime_seconds']:.1f}s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "verify"))
    args = parser.parse_args()
    if args.command == "run":
        run()
    elif args.command == "verify":
        verify_outputs(OUT_DIR)
        print("confidence sensitivity verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
