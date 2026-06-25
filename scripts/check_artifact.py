#!/usr/bin/env python
"""Lightweight artifact validator for the JISA review package."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "ARTIFACT.md",
    "REPRODUCIBILITY.md",
    "DATA.md",
    "MISSING_OBJECTS.md",
    "CITATION.cff",
    "LICENSE",
    "requirements.txt",
    "environment.yml",
    "Makefile",
    "docs/ARTIFACT_INVENTORY.md",
    "docs/TABLE_REPRODUCTION_MAP.md",
    "docs/RUNBOOK.md",
    "docs/LIMITATIONS_FOR_REVIEWERS.md",
    "paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex",
    "paper_eatvul_defense_framework/latex_submission/references.bib",
]

RESULT_COLUMNS = {
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

SECRET_PATTERNS = [".env", "id_rsa", "token", "credentials", "apikey", "api_key"]
KNOWN_LARGE_OK = {"Code and Dataset.zip", "model.zip"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_required_files() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    if missing:
        fail("missing required files: " + ", ".join(missing))
    print(f"Required files: {len(REQUIRED_FILES)} OK")


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
    print(f"Result files: {len(RESULT_COLUMNS)} OK")


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def check_data_splits() -> None:
    data_dir = ROOT / "Code and Dataset" / "file" / "data"
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
    for item in tracked:
        name = Path(item).name.lower()
        if any(pattern in name for pattern in SECRET_PATTERNS):
            suspicious.append(item)
        path = ROOT / item
        if path.exists() and path.is_file() and path.stat().st_size > 100 * 1024 * 1024:
            if item not in KNOWN_LARGE_OK:
                large.append(item)
    if suspicious:
        fail("tracked files look secret-like: " + ", ".join(suspicious))
    if large:
        warn("large tracked files require license/size review: " + ", ".join(large))
    print("Tracked-file hygiene: OK")


def main() -> int:
    check_required_files()
    check_result_columns()
    check_data_splits()
    check_missing_objects_doc()
    check_tracked_file_hygiene()
    print("Artifact check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
