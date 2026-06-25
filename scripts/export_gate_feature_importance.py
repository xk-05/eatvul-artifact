#!/usr/bin/env python
"""Export sample-gate random-forest feature-family importances for Table 6."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from eatvul_defense import DATASETS, OUT_DIR, BackgroundStats, load_jsonl, train_detector

HANDCRAFTED_FEATURES = [
    "log_length",
    "lexical_diversity",
    "rare_token_ratio",
    "unseen_token_ratio",
    "mean_token_idf",
    "p95_token_idf",
    "bigram_nll",
    "identifier_ratio",
    "repeated_name_ratio",
    "underscore_name_ratio",
    "digit_name_ratio",
    "control_ratio",
    "io_ratio",
    "type_ratio",
    "ast_struct_ratio",
    "leaf_node_ratio",
    "function_def_ratio",
    "selection_ratio",
    "iteration_ratio",
    "max_numeric_depth",
    "mean_numeric_depth",
    "longest_ast_struct_run",
    "longest_control_run",
]

FAMILIES = {
    "rare_token": ["rare_token_ratio"],
    "unseen_token": ["unseen_token_ratio"],
    "bigram_nll": ["bigram_nll"],
    "ast_structure": [
        "ast_struct_ratio",
        "leaf_node_ratio",
        "function_def_ratio",
        "selection_ratio",
        "iteration_ratio",
        "longest_ast_struct_run",
    ],
}

EXPECTED_LODO_AVERAGE = {
    "rare_token": 11.465514530883537,
    "unseen_token": 52.873029770370906,
    "bigram_nll": 14.540366125432438,
    "ast_structure": 21.121089573313114,
}


def train_lodo_gate(heldout: str):
    detector_train_items = []
    detector_adv_items = []
    for dataset, paths in DATASETS.items():
        if dataset == heldout:
            continue
        detector_train_items.extend(load_jsonl(paths["test"]))
        detector_adv_items.extend(load_jsonl(paths["adv"]))
    background = BackgroundStats([item["func"] for item in detector_train_items])
    detector = train_detector(detector_train_items, detector_adv_items, background)
    return detector


def family_importance_for_split(heldout: str) -> dict[str, float]:
    tfidf, _scaler, clf = train_lodo_gate(heldout)
    feature_importances = clf.feature_importances_
    offset = len(tfidf.get_feature_names_out())
    handcrafted = feature_importances[offset : offset + len(HANDCRAFTED_FEATURES)]
    by_feature = dict(zip(HANDCRAFTED_FEATURES, handcrafted))
    selected = {
        family: float(sum(by_feature[name] for name in names)) for family, names in FAMILIES.items()
    }
    total = sum(selected.values())
    if total <= 0:
        return {family: 0.0 for family in FAMILIES}
    return {family: value / total * 100.0 for family, value in selected.items()}


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["split", "rare_token", "unseen_token", "bigram_nll", "ast_structure"]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows = []
    for heldout in DATASETS:
        values = family_importance_for_split(heldout)
        rows.append({"split": f"heldout_{heldout}", **values})

    average = {family: float(np.mean([row[family] for row in rows])) for family in FAMILIES}
    rows.append({"split": "LODO_average", **average})

    output_path = OUT_DIR / "gate_feature_family_importance.csv"
    write_csv(rows, output_path)
    print(f"Wrote {output_path.relative_to(Path.cwd())}")

    mismatches = []
    for family, expected in EXPECTED_LODO_AVERAGE.items():
        actual = average[family]
        if abs(actual - expected) > 1e-9:
            mismatches.append(f"{family}: recorded_csv={expected:.12f}, recomputed={actual:.12f}")
    if mismatches:
        print("WARNING: recomputed LODO_average differs from the recorded CSV provenance:")
        for item in mismatches:
            print(f"  - {item}")
        print(
            "The CSV was written with the recomputed values; update Table 6 only after "
            "reviewing the provenance change."
        )
    else:
        print("Table 6 recomputation matches the recorded CSV provenance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
