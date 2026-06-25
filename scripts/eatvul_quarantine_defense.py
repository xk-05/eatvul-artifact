import argparse
import csv

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


OUT_DIR = ROOT / "results" / "eatvul_quarantine_defense"


def train_lodo_detector(name):
    train_items = []
    adv_items = []
    for other, paths in DATASETS.items():
        if other == name:
            continue
        train_items.extend(load_jsonl(paths["test"]))
        adv_items.extend(load_jsonl(paths["adv"]))
    background = BackgroundStats([item["func"] for item in train_items])
    detector = train_detector(train_items, adv_items, background)
    return detector, background


def calibrate_threshold(clean_scores, clean_pred, clean_y, clean_block_budget, only_predicted_benign):
    eligible = np.ones(len(clean_scores), dtype=bool)
    if only_predicted_benign:
        eligible &= clean_pred == 0
    if len(clean_y):
        # Calibrate primarily on clean non-vulnerable traffic, because these are the
        # samples most likely to become usability false alarms in a deployment gate.
        eligible &= clean_y == 0
    eligible_scores = clean_scores[eligible]
    if len(eligible_scores) == 0 or clean_block_budget <= 0:
        return float("inf")
    if clean_block_budget >= 1:
        return float(np.min(eligible_scores))
    return float(np.quantile(eligible_scores, 1.0 - clean_block_budget))


def quarantine(scores, pred, threshold, only_predicted_benign):
    blocked = scores >= threshold
    if only_predicted_benign:
        blocked &= pred == 0
    return blocked


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

    detector, detector_background = train_lodo_detector(name)
    clean_scores, _ = detector_predict(detector, clean_texts, detector_background)
    adv_scores, _ = detector_predict(detector, adv_texts, detector_background)

    threshold = calibrate_threshold(
        clean_scores,
        clean_pred,
        clean_y,
        args.clean_block_budget,
        args.only_predicted_benign,
    )
    clean_blocked = quarantine(clean_scores, clean_pred, threshold, args.only_predicted_benign)
    adv_blocked = quarantine(adv_scores, adv_pred, threshold, args.only_predicted_benign)

    baseline_success = adv_pred == 0
    residual_success = baseline_success & (~adv_blocked)

    clean_non_vul = clean_y == 0
    clean_vul = clean_y == 1
    row = {
        "dataset": name,
        "target_clean_acc": accuracy_score(clean_y, clean_pred),
        "target_clean_f1": f1_score(clean_y, clean_pred, zero_division=0),
        "threshold": threshold,
        "baseline_asr": float(np.mean(baseline_success)),
        "quarantine_asr": float(np.mean(residual_success)),
        "asr_reduction": float(np.mean(baseline_success) - np.mean(residual_success)),
        "adv_block_rate": float(np.mean(adv_blocked)),
        "adv_success_block_rate": float(np.mean(adv_blocked & baseline_success)),
        "clean_block_rate": float(np.mean(clean_blocked)),
        "clean_non_vul_block_rate": float(np.mean(clean_blocked[clean_non_vul])) if np.any(clean_non_vul) else 0.0,
        "clean_vul_block_rate": float(np.mean(clean_blocked[clean_vul])) if np.any(clean_vul) else 0.0,
        "mean_adv_score": float(np.mean(adv_scores)),
        "mean_clean_score": float(np.mean(clean_scores)),
    }
    return row


def fmt(value):
    if isinstance(value, float):
        if np.isinf(value):
            return "inf"
        return f"{value:.3f}"
    return str(value)


def print_table(rows):
    headers = [
        "dataset",
        "target_clean_f1",
        "baseline_asr",
        "quarantine_asr",
        "asr_reduction",
        "adv_block_rate",
        "clean_block_rate",
        "clean_non_vul_block_rate",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        print("| " + " | ".join(fmt(row[h]) for h in headers) + " |")


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = args.datasets or list(DATASETS)
    rows = [evaluate_dataset(name, args) for name in names]
    suffix = f"cleanblock{args.clean_block_budget:g}"
    if args.only_predicted_benign:
        suffix += "_benignonly"
    out_csv = OUT_DIR / f"quarantine_{suffix}_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print_table(rows)
    print(f"\nSaved: {out_csv}")


def main():
    parser = argparse.ArgumentParser(description="Block suspicious benign predictions to reduce EaTVul ASR.")
    parser.add_argument("--datasets", nargs="*", choices=DATASETS.keys())
    parser.add_argument("--clean-block-budget", type=float, default=0.10)
    parser.add_argument("--only-predicted-benign", action="store_true", default=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
