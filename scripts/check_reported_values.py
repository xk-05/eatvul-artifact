#!/usr/bin/env python
"""Check manuscript-reported aggregate values against result CSV files."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-3


@dataclass(frozen=True)
class Check:
    table: str
    file_name: str
    dataset: str
    column: str
    expected: float
    method: Optional[str] = None
    method_column: str = "method"


COLUMN_ALIASES = {
    "Clean F1 before": ["target_clean_f1", "clean_f1"],
    "Clean F1 after": ["defended_clean_f1", "sanitized_clean_f1", "component_clean_f1"],
    "Raw ASR": ["baseline_asr", "adv_asr"],
    "ADV recall": ["detector_recall_on_adv", "adv_recall"],
    "Clean FPR": ["detector_fpr_on_clean_non_vul", "clean_non_vul_fpr"],
    "Hard-override ASR": ["defended_asr"],
    "ASR change": ["asr_reduction"],
    "Post-deletion ASR": ["sanitized_asr", "component_asr"],
    "Clean F1": ["target_clean_f1", "clean_f1"],
    "Base ASR": ["baseline_asr"],
    "Residual silent-bypass": ["quarantine_asr"],
    "Quarantine rate": ["clean_block_rate"],
    "F1 before": ["target_clean_f1"],
    "F1 after": ["defended_clean_f1"],
    "F1 drop": ["clean_f1_drop"],
    "H.O. ASR": ["defended_asr"],
    "Clean modified": ["clean_modified_rate"],
    "ADV modified": ["adv_modified_rate"],
    "ADV removed ratio": ["adv_removed_ratio"],
    "Train n": ["train_n"],
    "ADV ASR": ["adv_asr"],
    "Bypassed": ["adv_bypassed"],
    "Gate recall on bypasses": ["gate_recall_on_neural_bypassed"],
}


def table4_checks() -> list[Check]:
    file_name = "results/eatvul_defense/lodo_calib_fpr_0.1_results.csv"
    rows = {
        "asterisk": (0.769, 0.455, 0.640, 0.280, 0.104, 0.360, 0.280),
        "openssl": (0.829, 0.693, 0.760, 0.740, 0.102, 0.120, 0.640),
        "cwe119": (0.944, 0.884, 0.720, 0.060, 0.100, 0.660, 0.060),
        "cwe399": (0.788, 0.721, 0.695, 0.070, 0.127, 0.625, 0.070),
    }
    columns = [
        "Clean F1 before",
        "Clean F1 after",
        "Raw ASR",
        "ADV recall",
        "Clean FPR",
        "Hard-override ASR",
        "ASR change",
    ]
    return [
        Check("Table 4", file_name, dataset, column, value)
        for dataset, values in rows.items()
        for column, value in zip(columns, values)
    ]


def table7_checks() -> list[Check]:
    file_name = "results/eatvul_anomaly_baselines/anomaly_baseline_results.csv"
    rows = [
        ("Supervised Gate", "openssl", 0.120, 0.640, 0.740),
        ("Supervised Gate", "asterisk", 0.360, 0.280, 0.280),
        ("Isolation Forest", "openssl", 0.740, 0.020, 0.080),
        ("Isolation Forest", "asterisk", 0.540, 0.100, 0.120),
        ("One-Class SVM", "openssl", 0.740, 0.020, 0.060),
        ("One-Class SVM", "asterisk", 0.580, 0.060, 0.100),
        ("Local Outlier Factor", "openssl", 0.740, 0.020, 0.060),
        ("Local Outlier Factor", "asterisk", 0.560, 0.080, 0.120),
        ("Mahalanobis", "openssl", 0.740, 0.020, 0.060),
        ("Mahalanobis", "asterisk", 0.600, 0.040, 0.160),
    ]
    columns = ["Hard-override ASR", "ASR change", "ADV recall"]
    return [
        Check("Table 7", file_name, dataset, column, value, method)
        for method, dataset, *values in rows
        for column, value in zip(columns, values)
    ]


def table8_checks() -> list[Check]:
    file_name = "results/neural_target_gate/neural_target_gate_results.csv"
    rows = {
        "openssl": (160, 0.436, 0.820, 41, 0.780),
        "asterisk": (150, 0.260, 0.480, 24, 0.542),
    }
    columns = ["Train n", "Clean F1", "ADV ASR", "Bypassed", "Gate recall on bypasses"]
    return [
        Check("Table 8", file_name, dataset, column, value, "CodeBERT-base", "victim")
        for dataset, values in rows.items()
        for column, value in zip(columns, values)
    ]


def table9_and_15_checks() -> list[Check]:
    window_file = (
        "results/eatvul_local_defense/"
        "localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv"
    )
    component_file = (
        "results/eatvul_component_defense/"
        "component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv"
    )
    table9_rows = [
        (window_file, "asterisk", 0.769, 0.274, 0.640, 0.600, 0.040),
        (window_file, "openssl", 0.829, 0.819, 0.760, 0.700, 0.060),
        (window_file, "cwe119", 0.944, 0.943, 0.720, 0.720, 0.000),
        (window_file, "cwe399", 0.788, 0.788, 0.695, 0.695, 0.000),
        (component_file, "asterisk", 0.769, 0.265, 0.640, 0.600, 0.040),
        (component_file, "openssl", 0.829, 0.829, 0.760, 0.760, 0.000),
        (component_file, "cwe119", 0.944, 0.941, 0.720, 0.720, 0.000),
        (component_file, "cwe399", 0.788, 0.780, 0.695, 0.695, 0.000),
    ]
    table9_cols = [
        "Clean F1 before",
        "Clean F1 after",
        "Raw ASR",
        "Post-deletion ASR",
        "ASR change",
    ]
    checks = [
        Check("Table 9", file_name, dataset, column, value)
        for file_name, dataset, *values in table9_rows
        for column, value in zip(table9_cols, values)
    ]

    table15_rows = [
        (window_file, "asterisk", 0.319, 0.040, 0.040, 0.040),
        (window_file, "openssl", 0.427, 0.760, 0.434, 0.060),
        (window_file, "cwe119", 0.144, 0.230, 0.207, 0.000),
        (window_file, "cwe399", 0.243, 0.375, 0.318, 0.000),
        (component_file, "asterisk", 0.381, 0.140, 0.066, 0.040),
        (component_file, "openssl", 0.404, 0.740, 0.311, 0.000),
        (component_file, "cwe119", 0.157, 0.270, 0.036, 0.000),
        (component_file, "cwe399", 0.247, 0.355, 0.061, 0.000),
    ]
    table15_cols = ["Clean modified", "ADV modified", "ADV removed ratio", "ASR change"]
    checks.extend(
        Check("Table 15", file_name, dataset, column, value)
        for file_name, dataset, *values in table15_rows
        for column, value in zip(table15_cols, values)
    )
    return checks


def table10_checks() -> list[Check]:
    file_name = "results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv"
    rows = {
        "asterisk": (0.769, 0.640, 0.360, 0.093),
        "openssl": (0.829, 0.760, 0.120, 0.085),
        "cwe119": (0.944, 0.720, 0.650, 0.059),
        "cwe399": (0.788, 0.695, 0.625, 0.082),
    }
    columns = ["Clean F1", "Base ASR", "Residual silent-bypass", "Quarantine rate"]
    return [
        Check("Table 10", file_name, dataset, column, value)
        for dataset, values in rows.items()
        for column, value in zip(columns, values)
    ]


def table11_checks() -> list[Check]:
    file_name = (
        "results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv"
    )
    rows = {
        "asterisk": (0.769, 0.741, 0.028, 0.640, 0.640, 0.000),
        "openssl": (0.829, 0.800, 0.029, 0.760, 0.520, 0.240),
        "cwe119": (0.944, 0.940, 0.003, 0.720, 0.710, 0.010),
        "cwe399": (0.788, 0.788, 0.000, 0.695, 0.695, 0.000),
    }
    columns = ["F1 before", "F1 after", "F1 drop", "Raw ASR", "H.O. ASR", "ASR change"]
    return [
        Check("Table 11", file_name, dataset, column, value)
        for dataset, values in rows.items()
        for column, value in zip(columns, values)
    ]


def resolve_column(df: pd.DataFrame, reported_column: str) -> str:
    aliases = COLUMN_ALIASES.get(reported_column, [reported_column])
    for column in aliases:
        if column in df.columns:
            return column
    raise KeyError(f"column {reported_column!r} not found; tried aliases {aliases}")


def select_row(df: pd.DataFrame, check: Check) -> pd.Series:
    mask = df["dataset"].astype(str).str.lower() == check.dataset.lower()
    if check.method is not None:
        mask &= df[check.method_column].astype(str) == check.method
    rows = df.loc[mask]
    if len(rows) != 1:
        raise ValueError(
            f"{check.file_name}: expected exactly one row for dataset={check.dataset} "
            f"method={check.method}, found {len(rows)}"
        )
    return rows.iloc[0]


def check_value(cache: dict[str, pd.DataFrame], check: Check) -> None:
    path = ROOT / check.file_name
    if not path.exists():
        raise FileNotFoundError(f"missing source file for {check.table}: {check.file_name}")
    if check.file_name not in cache:
        cache[check.file_name] = pd.read_csv(path)
    df = cache[check.file_name]
    column = resolve_column(df, check.column)
    row = select_row(df, check)
    actual = float(row[column])
    if not math.isclose(actual, check.expected, rel_tol=0.0, abs_tol=TOLERANCE):
        raise AssertionError(
            f"{check.table} mismatch: file={check.file_name}, dataset={check.dataset}, "
            f"method={check.method or '-'}, column={check.column} ({column}), "
            f"expected={check.expected:.3f}, actual={actual:.6f}"
        )


def main() -> int:
    checks: list[Check] = []
    checks.extend(table4_checks())
    checks.extend(table7_checks())
    checks.extend(table8_checks())
    checks.extend(table9_and_15_checks())
    checks.extend(table10_checks())
    checks.extend(table11_checks())

    cache: dict[str, pd.DataFrame] = {}
    for check in checks:
        check_value(cache, check)

    print(f"Reported-value check passed: {len(checks)} aggregate values within {TOLERANCE:g}.")
    print(
        "Table 6 verification skipped because the manuscript row predates a saved "
        "per-split feature-importance provenance file; run "
        "scripts/export_gate_feature_importance.py to recompute and compare it."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
