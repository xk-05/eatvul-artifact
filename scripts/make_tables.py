#!/usr/bin/env python
"""Create a lightweight table reproduction summary from aggregate CSVs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "tables"
OUT = OUT_DIR / "table_reproduction_summary.csv"

TABLES = [
    ("Table 4", "Sample-level gate", "results/eatvul_defense/lodo_calib_fpr_0.1_results.csv"),
    ("Table 7", "Anomaly baselines", "results/eatvul_anomaly_baselines/anomaly_baseline_results.csv"),
    ("Table 8", "Neural sanity check", "results/neural_target_gate/neural_target_gate_results.csv"),
    ("Table 9", "Fixed-window deletion", "results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv"),
    ("Table 9", "Component deletion", "results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv"),
    ("Table 10", "Quarantine", "results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv"),
    ("Table 11", "F1-constrained", "results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv"),
]


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for table, description, rel_path in TABLES:
        path = ROOT / rel_path
        rows.append(
            {
                "table": table,
                "description": description,
                "source_file": rel_path,
                "exists": str(path.exists()).lower(),
                "rows": row_count(path) if path.exists() else 0,
            }
        )
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["table", "description", "source_file", "exists", "rows"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
