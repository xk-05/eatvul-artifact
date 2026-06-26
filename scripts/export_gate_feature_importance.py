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
REQUIRED_EXTERNAL_SPLITS = ("test", "adv")


def display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def missing_external_split_paths() -> list[Path]:
    missing = []
    for paths in DATASETS.values():
        for split in REQUIRED_EXTERNAL_SPLITS:
            path = Path(paths[split])
            if not path.exists():
                missing.append(path)
    return missing


def packaged_lodo_average_mismatches(path: Path) -> list[str]:
    if not path.exists():
        return [f"{display_path(path)} is missing"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    average_row = next((row for row in rows if row.get("split") == "LODO_average"), None)
    if average_row is None:
        return [f"{display_path(path)} is missing the LODO_average row"]

    mismatches = []
    for family, expected in EXPECTED_LODO_AVERAGE.items():
        try:
            actual = float(average_row[family])
        except (KeyError, TypeError, ValueError):
            mismatches.append(f"{family}: packaged CSV has no numeric LODO_average value")
            continue
        if abs(actual - expected) > 1e-9:
            mismatches.append(f"{family}: expected={expected:.12f}, packaged={actual:.12f}")
    return mismatches


def keep_packaged_csv_when_external_data_missing(output_path: Path, missing: list[Path]) -> int:
    mismatches = packaged_lodo_average_mismatches(output_path)
    if mismatches:
        print("ERROR: external AST-token split files are missing and packaged CSV validation failed:")
        for item in mismatches:
            print(f"  - {item}")
        return 1

    print("External AST-token split files are not available; keeping packaged feature-family CSV.")
    print(f"Verified packaged LODO_average values in {display_path(output_path)}.")
    print(
        "To recompute this CSV, prepare the external split files under "
        "Code and Dataset/file/data/ as described in DATA.md."
    )
    if missing:
        print(f"Missing example: {display_path(missing[0])}")
    return 0


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
    output_path = OUT_DIR / "gate_feature_family_importance.csv"
    missing = missing_external_split_paths()
    if missing:
        return keep_packaged_csv_when_external_data_missing(output_path, missing)

    rows = []
    for heldout in DATASETS:
        values = family_importance_for_split(heldout)
        rows.append({"split": f"heldout_{heldout}", **values})

    average = {family: float(np.mean([row[family] for row in rows])) for family in FAMILIES}
    rows.append({"split": "LODO_average", **average})

    write_csv(rows, output_path)
    print(f"Wrote {display_path(output_path)}")

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
