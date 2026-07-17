#!/usr/bin/env python3
"""Materialize paper tables and vector figures from the verified evidence bundle."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "results" / "jisa_evidence_bundle.json"
LATEX_DIR = ROOT / "paper_eatvul_defense_framework" / "latex_submission"
GEN_DIR = LATEX_DIR / "generated"
FIG_DIR = ROOT / "paper_eatvul_defense_framework" / "figures_submission_jisa"
TARGETS = ("asterisk", "openssl", "cwe119", "cwe399")
METHODS = ("Supervised Gate", "Isolation Forest", "One-Class SVM", "Local Outlier Factor", "Mahalanobis")


def load_bundle(path: Path = BUNDLE_PATH) -> dict[str, object]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("verified") is not True:
        raise ValueError("evidence bundle is not verified")
    return bundle


def experiment_run(bundle: dict[str, object], name: str) -> dict[str, object]:
    for experiment in bundle["experiments"]:
        if experiment["experiment"] == name:
            completed = [run for run in experiment["runs"] if run.get("status") == "completed"]
            if not completed:
                raise ValueError(f"no completed run for {name}")
            return completed[0]
    raise KeyError(name)


def matched_summary(bundle: dict[str, object]) -> list[dict[str, str]]:
    rows = experiment_run(bundle, "matched_budget_quarantine")["summary"]
    if len(rows) != 100:
        raise ValueError("matched-budget grid must contain 100 rows")
    return rows


def tex_table(filename: str, caption: str, label: str, columns: str, header: str, rows: list[str], table_star: bool = False) -> None:
    env = "table*" if table_star else "table"
    text = [
        f"\\begin{{{env}}}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\scriptsize",
        f"\\begin{{tabular}}{{{columns}}}",
        "\\toprule",
        header + " \\\\ ",
        "\\midrule",
        *rows,
        "\\bottomrule",
        "\\end{tabular}",
        f"\\end{{{env}}}",
    ]
    (GEN_DIR / filename).write_text("\n".join(text) + "\n", encoding="utf-8")


def make_dataset_profile() -> None:
    rows = []
    for target in TARGETS:
        counts = []
        medians = []
        for split in ("train", "test", "test_ADV"):
            path = ROOT / "Code and Dataset" / "file" / "data" / f"{target}_ast_{split}.json"
            lengths = []
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        lengths.append(len(str(json.loads(line)["func"]).split()))
            counts.append(len(lengths))
            medians.append(int(np.median(lengths)))
        rows.append(
            f"{target.upper()} & {counts[0]} & {counts[1]} & {counts[2]} & "
            f"{medians[0]} & {medians[1]} & {medians[2]} \\\\"
        )
    tex_table(
        "jisa_dataset_profile.tex",
        "Dataset roles and median serialized AST-token lengths. ADV denotes the released adversarial test role.",
        "tab:dataset-profile",
        "lrrrrrr",
        "Target & Train & Test & ADV & Train med. & Test med. & ADV med.",
        rows,
        table_star=True,
    )


def make_matched_tables(frame: pd.DataFrame) -> None:
    five = frame[np.isclose(frame["nominal_budget"], 0.05)].copy()
    rows = []
    for target in TARGETS:
        part = five[five["target"] == target]
        for row in part.itertuples(index=False):
            rows.append(
                f"{target.upper()} & {row.method_family} & {int(row.clean_review_count)}/{int(row.clean_samples)} "
                f"({100*row.clean_review_rate:.1f}\\%) & {int(row.captured_adversarial_count)}/"
                f"{int(row.raw_adversarial_benign_count)} & {int(row.residual_silent_bypass_count)}/"
                f"{int(row.adv_samples)} \\\\"
            )
    tex_table(
        "jisa_matched_budget_5.tex",
        "Matched screening at the nominal 5\\% calibration budget. Counts are shown to avoid prevalence-dependent composites.",
        "tab:matched-five",
        "llrrr",
        "Target & Method & Unattacked review & Captured/bypass & Residual/all ADV",
        rows,
        table_star=True,
    )

    rank_records = []
    for target in TARGETS:
        part = five[five["target"] == target].copy()
        part["deviation"] = (part["clean_review_rate"] - 0.05).abs()
        part = part.sort_values(["captured_adversarial_count", "deviation", "method_family"], ascending=[False, True, True])
        for rank, method in enumerate(part["method_family"], 1):
            rank_records.append({"target": target, "method": method, "rank": rank})
    ranks = pd.DataFrame(rank_records)
    rows = []
    for method in METHODS:
        part = five[five["method_family"] == method]
        method_ranks = ranks[ranks["method"] == method]["rank"]
        rows.append(
            f"{method} & {100*part.clean_review_rate.min():.1f}--{100*part.clean_review_rate.max():.1f}\\% & "
            f"{100*(part.clean_review_rate-0.05).abs().max():.1f} pp & "
            f"{int(method_ranks.min())}--{int(method_ranks.max())} \\\\"
        )
    tex_table(
        "jisa_screening_stability.tex",
        "Cross-target operating stability at the nominal 5\\% budget.",
        "tab:screening-stability",
        "lrrr",
        "Method & Realized review range & Max. deviation & Rank span",
        rows,
    )


def make_codebert_table(bundle: dict[str, object]) -> None:
    rows = []
    for row in experiment_run(bundle, "codebert_validated_check")["summary"]:
        rows.append(
            f"{row['target'].upper()} & {int(row['model_selected_epoch'])} & {float(row['target_clean_precision']):.3f} & "
            f"{float(row['target_clean_recall']):.3f} & {float(row['baseline_clean_f1']):.3f} & "
            f"{float(row['baseline_asr']):.3f} & {float(row['defended_asr']):.3f} \\\\"
        )
    tex_table(
        "jisa_codebert_results.tex",
        "Bounded CodeBERT feasibility check. The 256-token prefix truncates most serialized inputs; these rows are not main efficacy evidence.",
        "tab:codebert-results",
        "lrrrrrr",
        "Target & Epoch & Precision & Recall & F1 & Raw bypass & Residual",
        rows,
    )


def make_deletion_table(bundle: dict[str, object]) -> None:
    frame = pd.DataFrame(experiment_run(bundle, "deletion_sensitivity_grid_combined")["summary"])
    numeric = ["asr_reduction", "baseline_clean_f1", "sanitized_clean_f1"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column])
    frame["clean_f1_drop"] = frame["baseline_clean_f1"] - frame["sanitized_clean_f1"]
    rows = []
    for target in TARGETS:
        for method in ("localize", "component"):
            part = frame[(frame["target"] == target) & (frame["method"] == method)]
            feasible = part[part["clean_f1_drop"] <= 0.03 + 1e-12]
            best = "--" if feasible.empty else f"{100*feasible.asr_reduction.max():.1f}\\%"
            rows.append(
                f"{target.upper()} & {method} & {len(part)} & {100*part.asr_reduction.median():.1f}\\% & "
                f"{100*part.asr_reduction.quantile(.25):.1f}--{100*part.asr_reduction.quantile(.75):.1f}\\% & {best} \\\\"
            )
    tex_table(
        "jisa_deletion_sensitivity.tex",
        "Full fixed deletion grid. Best feasible is the largest reduction with clean-F1 drop at most 0.03 and is exploratory, not selected for deployment.",
        "tab:deletion-sensitivity",
        "llrrrr",
        "Target & Diagnostic & Cells & Median & IQR & Best feasible",
        rows,
        table_star=True,
    )


def make_curves(frame: pd.DataFrame) -> None:
    colors = dict(zip(METHODS, plt.get_cmap("tab10").colors[: len(METHODS)]))
    for kind in ("capture", "residual"):
        fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
        for ax, target in zip(axes.flat, TARGETS):
            part = frame[frame["target"] == target]
            for method in METHODS:
                line = part[part["method_family"] == method].sort_values("nominal_budget")
                y = line["attack_capture_rate"] if kind == "capture" else line["residual_silent_bypass_rate"]
                ax.plot(line["clean_review_rate"], y, marker="o", ms=3, lw=1.4, color=colors[method], label=method)
            ax.set_title(target.upper())
            ax.grid(alpha=.25)
            ax.set_xlim(0, .20)
            ax.set_ylim(0, .75)
        for ax in axes[-1, :]:
            ax.set_xlabel("Realized unattacked review rate")
        for ax in axes[:, 0]:
            ax.set_ylabel("Adversarial capture rate" if kind == "capture" else "Residual silent-bypass rate")
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False)
        fig.tight_layout(rect=(0, .09, 1, 1))
        fig.savefig(FIG_DIR / f"{kind}_vs_review.pdf", bbox_inches="tight")
        plt.close(fig)


def make_boundary() -> None:
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.axis("off")
    boxes = [
        ("Observed evidence", "AST-token sequence\nTarget output"),
        ("Identifiable", "Scores, review load\nCapture, residual bypass"),
        ("Supported action", "Target-calibrated\nquarantine / review"),
        ("Not identified", "Inserted source span\nSafe automatic repair"),
    ]
    colors = ("#dbeafe", "#dcfce7", "#fef3c7", "#fee2e2")
    for index, ((title, body), color) in enumerate(zip(boxes, colors)):
        x = .02 + index * .245
        patch = FancyBboxPatch((x, .2), .205, .58, boxstyle="round,pad=0.02", fc=color, ec="#334155", lw=1.2)
        ax.add_patch(patch)
        ax.text(x + .1025, .62, title, ha="center", va="center", weight="bold", fontsize=10)
        ax.text(x + .1025, .39, body, ha="center", va="center", fontsize=9)
        if index < len(boxes) - 1:
            ax.annotate("", xy=(x + .245, .49), xytext=(x + .21, .49), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(.5, .06, "Source-aware localization, compilation, and security/functional validation are required before a repair claim.", ha="center", fontsize=9)
    fig.savefig(FIG_DIR / "action_boundary.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle()
    frame = pd.DataFrame(matched_summary(bundle))
    numeric = [
        "nominal_budget", "clean_review_rate", "clean_review_count", "clean_samples",
        "captured_adversarial_count", "raw_adversarial_benign_count", "residual_silent_bypass_count",
        "adv_samples", "attack_capture_rate", "residual_silent_bypass_rate", "coverage",
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column])
    make_dataset_profile()
    make_matched_tables(frame)
    make_codebert_table(bundle)
    make_deletion_table(bundle)
    make_curves(frame)
    make_boundary()
    frame.to_csv(ROOT / "results" / "jisa_matched_budget_summary.csv", index=False)
    print("materialized verified JISA tables and figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
