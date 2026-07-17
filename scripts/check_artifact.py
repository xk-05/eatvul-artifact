#!/usr/bin/env python
"""Lightweight artifact validator for the JISA review package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "ARTIFACT.md",
    "REPRODUCIBILITY.md",
    "DATA.md",
    "THIRD_PARTY_DATA.md",
    "MISSING_OBJECTS.md",
    "CITATION.cff",
    "LICENSE",
    "requirements.txt",
    "environment.yml",
    "pyproject.toml",
    "Makefile",
    "docs/ARTIFACT_INVENTORY.md",
    "docs/TABLE_REPRODUCTION_MAP.md",
    "docs/RUNBOOK.md",
    "docs/LIMITATIONS_FOR_REVIEWERS.md",
    "data/README.md",
    "scripts/check_reported_values.py",
    "scripts/export_gate_feature_importance.py",
    "scripts/materialize_jisa_evidence.py",
    "scripts/jisa_confidence_sensitivity.py",
    "paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex",
    "paper_eatvul_defense_framework/latex_submission/main_jisa.tex",
    "paper_eatvul_defense_framework/latex_submission/main_jisa.pdf",
    "paper_eatvul_defense_framework/latex_submission/references.bib",
    "paper_eatvul_defense_framework/figures_submission_jisa/action_boundary.pdf",
    "paper_eatvul_defense_framework/figures_submission_jisa/capture_vs_review.pdf",
    "paper_eatvul_defense_framework/figures_submission_jisa/residual_vs_review.pdf",
    "results/jisa_evidence_bundle.json",
    "results/jisa_matched_budget_summary.csv",
    "results/jisa_confidence_sensitivity/confidence_adv_samples.csv",
    "results/jisa_confidence_sensitivity/confidence_summary.csv",
    "results/jisa_confidence_sensitivity/duplicate_sensitivity.csv",
    "results/jisa_confidence_sensitivity/token_length_profile.csv",
    "manifests/jisa_final/FINAL_RUN_MANIFEST.json",
    "manifests/jisa_final/confidence_run_manifest.json",
    "highlights.md",
]

REQUIRED_FINAL_TABLES = [
    "jisa_dataset_profile.tex",
    "jisa_matched_budget_5.tex",
    "jisa_confidence_baseline.tex",
    "jisa_duplicate_sensitivity.tex",
    "jisa_screening_stability.tex",
    "jisa_codebert_results.tex",
    "jisa_token_length.tex",
    "jisa_deletion_sensitivity.tex",
]

CONFIG_FILES = {
    "results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_config.json": {
        "script": "scripts/eatvul_localize_sanitize.py",
        "min_prob_gain": 0.005,
        "benign_only_gating": True,
        "sample_level_gate_used": False,
    },
    "results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_config.json": {
        "script": "scripts/eatvul_component_sanitize.py",
        "min_prob_gain": 0.001,
        "benign_only_gating": True,
        "sample_level_gate_used": False,
    },
}

RESULT_COLUMNS = {
    "results/jisa_confidence_sensitivity/confidence_summary.csv": {
        "dataset",
        "budget",
        "calibration_n",
        "test_review_rate",
        "adv_benign_predictions",
        "adv_captured",
        "residual_silent_bypass_rate",
    },
    "results/jisa_matched_budget_summary.csv": {
        "target",
        "method_family",
        "nominal_budget",
        "clean_review_rate",
        "captured_adversarial_count",
        "residual_silent_bypass_rate",
    },
    "results/eatvul_defense/lodo_calib_fpr_0.1_results.csv": {
        "dataset",
        "target_clean_f1",
        "defended_clean_f1",
        "baseline_asr",
        "defended_asr",
        "asr_reduction",
    },
    "results/eatvul_anomaly_baselines/anomaly_baseline_results.csv": {
        "dataset",
        "method",
        "baseline_asr",
        "defended_asr",
        "asr_reduction",
        "adv_recall",
    },
    "results/neural_target_gate/neural_target_gate_results.csv": {
        "dataset",
        "victim",
        "clean_f1",
        "adv_asr",
        "adv_bypassed",
        "gate_recall_on_neural_bypassed",
    },
    "results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv": {
        "dataset",
        "target_clean_f1",
        "sanitized_clean_f1",
        "baseline_asr",
        "sanitized_asr",
        "asr_reduction",
    },
    "results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv": {
        "dataset",
        "target_clean_f1",
        "component_clean_f1",
        "baseline_asr",
        "component_asr",
        "asr_reduction",
    },
    "results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv": {
        "dataset",
        "target_clean_f1",
        "baseline_asr",
        "quarantine_asr",
        "clean_block_rate",
    },
    "results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv": {
        "dataset",
        "target_clean_f1",
        "defended_clean_f1",
        "clean_f1_drop",
        "baseline_asr",
        "defended_asr",
        "asr_reduction",
    },
}

DATA_SPLITS = {
    "asterisk": (880, 367, 50),
    "openssl": (520, 213, 50),
    "cwe119": (5670, 2451, 200),
    "cwe399": (545, 255, 200),
}

MISSING_OBJECT_TERMS = [
    "true inserted spans",
    "source diffs",
    "source-to-token mappings",
    "CFGs",
    "PDGs",
    "compiler-validated adaptive snippets",
    "complete paired prediction logs",
]

SECRET_PATTERNS = [".env", "id_rsa", "credentials", "apikey", "api_key"]
PROHIBITED_TRACKED_FILES = {"Code and Dataset.zip"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_required_files() -> None:
    required = list(REQUIRED_FILES)
    required.extend(
        f"paper_eatvul_defense_framework/latex_submission/generated/{name}"
        for name in REQUIRED_FINAL_TABLES
    )
    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        fail("missing required files: " + ", ".join(missing))
    print(f"Required files: {len(required)} OK")


def check_result_columns() -> None:
    for file_name, expected in RESULT_COLUMNS.items():
        path = ROOT / file_name
        if not path.exists():
            fail(f"missing result file: {file_name}")
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            rows = list(reader)
        missing = sorted(expected - columns)
        if missing:
            fail(f"{file_name} missing columns: {', '.join(missing)}")
        if not rows:
            fail(f"{file_name} has no rows")
        if file_name.endswith("confidence_summary.csv"):
            datasets = {row["dataset"].lower() for row in rows}
            budgets = {float(row["budget"]) for row in rows}
            if datasets != set(DATA_SPLITS):
                fail(f"{file_name} does not contain all four targets")
            if budgets != {0.01, 0.03, 0.05, 0.1, 0.15}:
                fail(f"{file_name} has unexpected budgets: {sorted(budgets)}")
    print(f"Result files: {len(RESULT_COLUMNS)} OK")


def check_config_sidecars() -> None:
    for file_name, expected in CONFIG_FILES.items():
        path = ROOT / file_name
        if not path.exists():
            fail(f"missing config sidecar: {file_name}")
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{file_name} is not valid JSON: {exc}")
        for key, value in expected.items():
            if config.get(key) != value:
                fail(f"{file_name} has {key}={config.get(key)!r}, expected {value!r}")
    print(f"Config sidecars: {len(CONFIG_FILES)} OK")


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def check_data_splits() -> None:
    data_dir = ROOT / "Code and Dataset" / "file" / "data"
    expected_paths = [
        data_dir / f"{dataset}_ast_{suffix}.json"
        for dataset in DATA_SPLITS
        for suffix in ["train", "test", "test_ADV"]
    ]
    present = [path for path in expected_paths if path.exists()]
    if not present:
        print("Dataset split counts: external AST-token splits not bundled; see DATA.md")
        return
    missing = [rel(path) for path in expected_paths if not path.exists()]
    if missing:
        fail("partial external AST-token split set is missing: " + ", ".join(missing))
    for dataset, expected in DATA_SPLITS.items():
        observed = []
        for suffix in ["train", "test", "test_ADV"]:
            observed.append(count_jsonl(data_dir / f"{dataset}_ast_{suffix}.json"))
        if tuple(observed) != expected:
            fail(f"{dataset} split counts {observed} != expected {expected}")
    print(f"Dataset split counts: {len(DATA_SPLITS)} OK")


def check_missing_objects_doc() -> None:
    text = (ROOT / "MISSING_OBJECTS.md").read_text(encoding="utf-8")
    absent = [term for term in MISSING_OBJECT_TERMS if term not in text]
    if absent:
        fail("MISSING_OBJECTS.md does not mention: " + ", ".join(absent))
    print("Missing-object documentation: OK")


def git_ls_files() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except Exception as exc:  # pragma: no cover - git may be absent in archives.
        warn(f"could not inspect tracked files with git: {exc}")
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def check_tracked_file_hygiene() -> None:
    tracked = git_ls_files()
    if not tracked:
        return
    suspicious = []
    large = []
    prohibited = []
    for item in tracked:
        name = Path(item).name.lower()
        if any(pattern in name for pattern in SECRET_PATTERNS):
            suspicious.append(item)
        if Path(item).name in PROHIBITED_TRACKED_FILES:
            prohibited.append(item)
        path = ROOT / item
        if path.exists() and path.is_file() and path.stat().st_size > 100 * 1024 * 1024:
            large.append(item)
    if prohibited:
        fail("prohibited private release files are tracked: " + ", ".join(prohibited))
    if suspicious:
        fail("tracked files look secret-like: " + ", ".join(suspicious))
    if large:
        warn("large tracked files require license/size review: " + ", ".join(large))
    print("Tracked-file hygiene: OK")


def main() -> int:
    check_required_files()
    check_result_columns()
    check_config_sidecars()
    check_data_splits()
    check_missing_objects_doc()
    check_tracked_file_hygiene()
    print("Artifact check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
