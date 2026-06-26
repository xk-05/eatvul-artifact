#!/usr/bin/env python
"""Verify expected manuscript figure assets and write an inventory."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper_eatvul_defense_framework" / "figures_submission"
OUT_DIR = ROOT / "results" / "figures"
OUT = OUT_DIR / "figure_inventory.csv"

FIGURES = [
    "dataset_overview_en.png",
    "sample_gate_results_en.png",
    "gate_feature_contribution_en.png",
    "window_sanitize_results_en.png",
    "component_sanitize_results_en.png",
    "deployment_tradeoff_en.png",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    missing = []
    for name in FIGURES:
        path = FIG_DIR / name
        if not path.exists():
            missing.append(name)
        rows.append(
            {
                "figure_file": f"paper_eatvul_defense_framework/figures_submission/{name}",
                "exists": str(path.exists()).lower(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["figure_file", "exists", "bytes"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    if missing:
        raise SystemExit("Missing figure files: " + ", ".join(missing))
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
