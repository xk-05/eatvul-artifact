import argparse
import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

from eatvul_defense import (
    DATASETS,
    ROOT,
    BackgroundStats,
    detector_predict,
    load_jsonl,
    texts_labels,
    train_detector,
    train_target,
)


OUT_DIR = ROOT / "results" / "eatvul_f1_constrained_defense"


def candidate_thresholds(scores):
    unique = np.unique(scores)
    if len(unique) > 200:
        qs = np.linspace(0.0, 1.0, 201)
        unique = np.unique(np.quantile(scores, qs))
    return sorted(set([float("inf"), *map(float, unique)]), reverse=True)


def apply_defense(target_pred, detector_scores, threshold, only_predicted_benign=True):
    defended = target_pred.copy()
    suspicious = detector_scores >= threshold
    if only_predicted_benign:
        suspicious = suspicious & (target_pred == 0)
    defended[suspicious] = 1
    return defended, suspicious.astype(int)


def train_lodo_detector(name):
    detector_train_items = []
    detector_adv_items = []
    for other, paths in DATASETS.items():
        if other == name:
            continue
        detector_train_items.extend(load_jsonl(paths["test"]))
        detector_adv_items.extend(load_jsonl(paths["adv"]))
    background = BackgroundStats([item["func"] for item in detector_train_items])
    detector = train_detector(detector_train_items, detector_adv_items, background)
    return detector, background


def select_threshold(clean_y, clean_pred, clean_scores, base_f1, max_f1_drop, only_predicted_benign):
    min_allowed_f1 = max(0.0, base_f1 - max_f1_drop)
    best = None
    for threshold in candidate_thresholds(clean_scores):
        defended_pred, clean_detected = apply_defense(clean_pred, clean_scores, threshold, only_predicted_benign)
        defended_f1 = f1_score(clean_y, defended_pred, zero_division=0)
        if defended_f1 + 1e-12 < min_allowed_f1:
            continue
        clean_change_rate = float(np.mean(defended_pred != clean_pred))
        clean_non_vul_fpr = float(np.mean(clean_detected[clean_y == 0])) if np.any(clean_y == 0) else 0.0
        candidate = {
            "threshold": threshold,
            "defended_clean_f1": defended_f1,
            "clean_change_rate": clean_change_rate,
            "clean_non_vul_fpr": clean_non_vul_fpr,
        }
        # Among thresholds that satisfy clean F1, choose the most aggressive one.
        if best is None or candidate["threshold"] < best["threshold"]:
            best = candidate
    if best is None:
        return {
            "threshold": float("inf"),
            "defended_clean_f1": base_f1,
            "clean_change_rate": 0.0,
            "clean_non_vul_fpr": 0.0,
        }
    return best


def evaluate_dataset(name, args):
    paths = DATASETS[name]
    train_items = load_jsonl(paths["train"])
    test_items = load_jsonl(paths["test"])
    adv_items = load_jsonl(paths["adv"])

    target = train_target(train_items)
    clean_texts, clean_y = texts_labels(test_items)
    adv_texts, _ = texts_labels(adv_items)

    clean_pred = target.predict(clean_texts)
    adv_pred = target.predict(adv_texts)
    base_clean_acc = accuracy_score(clean_y, clean_pred)
    base_clean_f1 = f1_score(clean_y, clean_pred, zero_division=0)
    baseline_asr = float(np.mean(adv_pred == 0))

    detector, detector_background = train_lodo_detector(name)
    clean_scores, _ = detector_predict(detector, clean_texts, detector_background)
    adv_scores, _ = detector_predict(detector, adv_texts, detector_background)

    chosen = select_threshold(
        clean_y,
        clean_pred,
        clean_scores,
        base_clean_f1,
        args.max_clean_f1_drop,
        args.only_predicted_benign,
    )
    defended_clean_pred, clean_detected = apply_defense(
        clean_pred, clean_scores, chosen["threshold"], args.only_predicted_benign
    )
    defended_adv_pred, adv_detected = apply_defense(
        adv_pred, adv_scores, chosen["threshold"], args.only_predicted_benign
    )

    defended_clean_f1 = f1_score(clean_y, defended_clean_pred, zero_division=0)
    defended_asr = float(np.mean(defended_adv_pred == 0))
    adv_recall = float(np.mean(adv_detected)) if len(adv_detected) else 0.0
    clean_non_vul_fpr = float(np.mean(clean_detected[clean_y == 0])) if np.any(clean_y == 0) else 0.0
    clean_vul_change = float(np.mean(clean_detected[clean_y == 1])) if np.any(clean_y == 1) else 0.0

    return {
        "dataset": name,
        "target_clean_acc": base_clean_acc,
        "target_clean_f1": base_clean_f1,
        "defended_clean_f1": defended_clean_f1,
        "clean_f1_drop": base_clean_f1 - defended_clean_f1,
        "threshold": chosen["threshold"],
        "baseline_asr": baseline_asr,
        "defended_asr": defended_asr,
        "asr_reduction": baseline_asr - defended_asr,
        "adv_recall": adv_recall,
        "clean_non_vul_fpr": clean_non_vul_fpr,
        "clean_vul_change_rate": clean_vul_change,
        "mean_adv_score": float(np.mean(adv_scores)),
        "mean_clean_score": float(np.mean(clean_scores)),
    }


def fmt(value):
    if isinstance(value, float):
        if np.isinf(value):
            return "inf"
        return f"{value:.3f}"
    return str(value)


def print_markdown_table(rows):
    headers = [
        "dataset",
        "target_clean_f1",
        "defended_clean_f1",
        "clean_f1_drop",
        "baseline_asr",
        "defended_asr",
        "asr_reduction",
        "adv_recall",
        "clean_non_vul_fpr",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        print("| " + " | ".join(fmt(row[h]) for h in headers) + " |")


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = args.datasets or list(DATASETS)
    rows = [evaluate_dataset(name, args) for name in names]
    suffix = f"maxf1drop{args.max_clean_f1_drop:g}"
    if args.only_predicted_benign:
        suffix += "_benignonly"
    out_csv = OUT_DIR / f"f1_constrained_{suffix}_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print_markdown_table(rows)
    print(f"\nSaved: {out_csv}")


def main():
    parser = argparse.ArgumentParser(description="Lower EaTVul ASR while constraining clean F1 degradation.")
    parser.add_argument("--datasets", nargs="*", choices=DATASETS.keys())
    parser.add_argument("--max-clean-f1-drop", type=float, default=0.02)
    parser.add_argument("--only-predicted-benign", action="store_true", default=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
