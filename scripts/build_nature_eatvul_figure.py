"""Build a Nature-style multi-panel figure for EaTVul defense experiments.

Outputs:
  reports/nature_figures/eatvul_defense_nature.svg
  reports/nature_figures/eatvul_defense_nature.png
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "nature_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(OUT_DIR / ".mplconfig"))

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


DATASETS = ["asterisk", "openssl", "cwe119", "cwe399"]
DATASET_LABELS = {
    "asterisk": "Asterisk",
    "openssl": "OpenSSL",
    "cwe119": "CWE119",
    "cwe399": "CWE399",
}

METHOD_ORDER = [
    "Baseline",
    "Sample gate",
    "Quarantine",
    "F1-constrained",
    "Window sanitize",
    "Component sanitize",
]

PALETTE = {
    "Baseline": "#4D4D4D",
    "Sample gate": "#0F4D92",
    "Quarantine": "#B64342",
    "F1-constrained": "#42949E",
    "Window sanitize": "#8BCF8B",
    "Component sanitize": "#FFD700",
    "axis": "#272727",
    "grid": "#D8D8D8",
    "soft": "#F4F4F4",
}


def apply_publication_style() -> None:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"]
    plt.rcParams["svg.fonttype"] = "none"
    mpl.rcParams.update(
        {
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.labelsize": 7,
            "axes.titlesize": 8,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def read_csv(rel_path: str) -> pd.DataFrame:
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Missing source data: {path}")
    return pd.read_csv(path)


def assemble_long_table() -> pd.DataFrame:
    sample = read_csv("results/eatvul_defense/lodo_calib_fpr_0.1_results.csv")
    quarantine = read_csv("results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv")
    f1 = read_csv("results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv")
    window = read_csv(
        "results/eatvul_local_defense/"
        "localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv"
    )
    component = read_csv(
        "results/eatvul_component_defense/"
        "component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv"
    )

    tables: list[pd.DataFrame] = []
    base = sample[["dataset", "baseline_asr", "target_clean_f1", "adv_samples"]].copy()
    base["method"] = "Baseline"
    base["residual_asr"] = base["baseline_asr"]
    base["asr_reduction"] = 0.0
    base["clean_f1"] = base["target_clean_f1"]
    base["clean_f1_drop"] = 0.0
    base["clean_cost"] = 0.0
    tables.append(base)

    method_specs = [
        ("Sample gate", sample, "defended_asr", "defended_clean_f1", "detector_fpr_on_clean_non_vul"),
        ("Quarantine", quarantine, "quarantine_asr", "target_clean_f1", "clean_block_rate"),
        ("F1-constrained", f1, "defended_asr", "defended_clean_f1", "clean_f1_drop"),
        ("Window sanitize", window, "sanitized_asr", "sanitized_clean_f1", "clean_modified_rate"),
        ("Component sanitize", component, "component_asr", "component_clean_f1", "clean_modified_rate"),
    ]
    for method, frame, asr_col, clean_col, cost_col in method_specs:
        current = frame[["dataset", "baseline_asr", "target_clean_f1"]].copy()
        current["method"] = method
        current["residual_asr"] = frame[asr_col]
        current["asr_reduction"] = frame["baseline_asr"] - frame[asr_col]
        current["clean_f1"] = frame[clean_col]
        current["clean_f1_drop"] = frame["target_clean_f1"] - frame[clean_col]
        current["clean_cost"] = frame[cost_col]
        current["adv_samples"] = current["dataset"].map(base.set_index("dataset")["adv_samples"])
        tables.append(current)

    out = pd.concat(tables, ignore_index=True)
    out["dataset_label"] = out["dataset"].map(DATASET_LABELS)
    out["method"] = pd.Categorical(out["method"], categories=METHOD_ORDER, ordered=True)
    out["dataset"] = pd.Categorical(out["dataset"], categories=DATASETS, ordered=True)
    return out.sort_values(["method", "dataset"]).reset_index(drop=True)


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        color=PALETTE["axis"],
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.tick_params(axis="both", length=2.5, color=PALETTE["axis"])
    ax.spines["left"].set_color(PALETTE["axis"])
    ax.spines["bottom"].set_color(PALETTE["axis"])


def panel_residual_asr(ax: plt.Axes, data: pd.DataFrame) -> None:
    chosen = ["Baseline", "Quarantine", "F1-constrained", "Sample gate"]
    x = np.arange(len(DATASETS))
    width = 0.18
    for index, method in enumerate(chosen):
        values = (
            data[data["method"] == method]
            .set_index("dataset")
            .loc[DATASETS, "residual_asr"]
            .to_numpy()
        )
        offset = (index - (len(chosen) - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            values,
            width=width,
            label=method,
            color=PALETTE[method],
            edgecolor="white",
            linewidth=0.35,
        )
        if method in {"Quarantine", "F1-constrained"}:
            for bar, value in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value + 0.018,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=5.5,
                    color=PALETTE["axis"],
                )
    ax.set_ylim(0, 0.86)
    ax.set_xticks(x)
    ax.set_xticklabels([DATASET_LABELS[d] for d in DATASETS], rotation=0)
    ax.set_ylabel("Residual attack success rate")
    ax.set_title("Sample-level defenses provide the clearest ASR suppression", loc="left", pad=6)
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.45, alpha=0.6)
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(-0.01, 1.0), handlelength=1.0, columnspacing=0.8)
    clean_axes(ax)
    add_panel_label(ax, "a")


def panel_heatmap(ax: plt.Axes, data: pd.DataFrame) -> None:
    matrix = (
        data.pivot(index="method", columns="dataset", values="residual_asr")
        .loc[METHOD_ORDER, DATASETS]
        .to_numpy()
    )
    cmap = LinearSegmentedColormap.from_list(
        "asr_risk",
        ["#F7FBF7", "#DDF3DE", "#F6CFCB", "#B64342"],
    )
    image = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=0.8)
    ax.set_xticks(np.arange(len(DATASETS)))
    ax.set_xticklabels([DATASET_LABELS[d] for d in DATASETS])
    ax.set_yticks(np.arange(len(METHOD_ORDER)))
    ax.set_yticklabels(METHOD_ORDER)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            color = "white" if value >= 0.58 else PALETTE["axis"]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=5.7, color=color)
    ax.set_title("Residual ASR across all evaluated defenses", loc="left", pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    cbar = plt.colorbar(image, ax=ax, fraction=0.045, pad=0.025)
    cbar.set_label("Residual ASR", rotation=270, labelpad=10)
    cbar.outline.set_visible(False)
    add_panel_label(ax, "b")


def panel_clean_f1(ax: plt.Axes, data: pd.DataFrame) -> None:
    chosen = ["Baseline", "Quarantine", "F1-constrained", "Sample gate"]
    x = np.arange(len(DATASETS))
    width = 0.18
    for index, method in enumerate(chosen):
        values = (
            data[data["method"] == method]
            .set_index("dataset")
            .loc[DATASETS, "clean_f1"]
            .to_numpy()
        )
        offset = (index - (len(chosen) - 1) / 2) * width
        ax.bar(
            x + offset,
            values,
            width=width,
            label=method,
            color=PALETTE[method],
            edgecolor="white",
            linewidth=0.35,
        )
    ax.set_ylim(0.2, 1.02)
    ax.set_xticks(x)
    ax.set_xticklabels([DATASET_LABELS[d] for d in DATASETS])
    ax.set_ylabel("Clean F1")
    ax.set_title("Clean performance is preserved by block/threshold strategies", loc="left", pad=6)
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.45, alpha=0.6)
    clean_axes(ax)
    add_panel_label(ax, "c")


def panel_tradeoff(ax: plt.Axes, data: pd.DataFrame) -> None:
    methods = [method for method in METHOD_ORDER if method != "Baseline"]
    markers = {"asterisk": "o", "openssl": "s", "cwe119": "^", "cwe399": "D"}
    for method in methods:
        subset = data[data["method"] == method]
        for dataset in DATASETS:
            row = subset[subset["dataset"] == dataset].iloc[0]
            ax.scatter(
                row["clean_cost"],
                row["asr_reduction"],
                s=34,
                marker=markers[dataset],
                color=PALETTE[method],
                edgecolor="white",
                linewidth=0.5,
                alpha=0.95,
            )

    ax.axhline(0, color=PALETTE["axis"], lw=0.6)
    ax.axvline(0.1, color=PALETTE["grid"], lw=0.7, ls="--")
    ax.set_xlim(-0.015, 0.48)
    ax.set_ylim(-0.035, 0.68)
    ax.set_xlabel("Clean-sample cost")
    ax.set_ylabel("ASR reduction")
    ax.set_title("Security gain versus deployment cost", loc="left", pad=6)
    ax.grid(color=PALETTE["grid"], lw=0.45, alpha=0.55)
    method_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PALETTE[m], markeredgecolor="white", markersize=5, label=m)
        for m in methods
    ]
    dataset_handles = [
        Line2D([0], [0], marker=markers[d], color=PALETTE["axis"], linestyle="none", markersize=4.5, label=DATASET_LABELS[d])
        for d in DATASETS
    ]
    first_legend = ax.legend(
        handles=method_handles,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.0),
        handletextpad=0.3,
        borderpad=0.2,
        labelspacing=0.25,
    )
    ax.add_artist(first_legend)
    ax.legend(
        handles=dataset_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.32),
        handletextpad=0.3,
        borderpad=0.2,
        labelspacing=0.25,
    )
    clean_axes(ax)
    add_panel_label(ax, "d")


def add_figure_note(fig: plt.Figure, data: pd.DataFrame) -> None:
    n_by_dataset = (
        data[data["method"] == "Baseline"]
        .set_index("dataset")
        .loc[DATASETS, "adv_samples"]
        .astype(int)
        .to_dict()
    )
    note = (
        "Source data: EaTVul defense CSV outputs. "
        "ASR, attack success rate; lower residual ASR and higher Clean F1 are better. "
        "Clean-sample cost denotes clean block rate, clean F1 drop, clean modification rate, or detector FPR "
        "according to the defense action. "
        "Adversarial n: "
        + ", ".join(f"{DATASET_LABELS[k]}={v}" for k, v in n_by_dataset.items())
        + "."
    )
    fig.text(0.02, 0.012, note, ha="left", va="bottom", fontsize=5.8, color="#555555")


def build_figure(data: pd.DataFrame) -> plt.Figure:
    fig = plt.figure(figsize=(7.2, 5.35), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.08, 1.0],
        width_ratios=[1.15, 1.0],
        left=0.075,
        right=0.985,
        top=0.89,
        bottom=0.11,
        wspace=0.32,
        hspace=0.45,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[1, 0])
    ax_d = fig.add_subplot(grid[1, 1])
    panel_residual_asr(ax_a, data)
    panel_heatmap(ax_b, data)
    panel_clean_f1(ax_c, data)
    panel_tradeoff(ax_d, data)
    fig.suptitle("Defense trade-offs against EaTVul insertion attacks", x=0.075, y=0.975, ha="left", fontsize=9.5)
    add_figure_note(fig, data)
    return fig


def save_outputs(fig: plt.Figure, stem: str = "eatvul_defense_nature") -> tuple[Path, Path, Path]:
    svg_path = OUT_DIR / f"{stem}.svg"
    png_path = OUT_DIR / f"{stem}.png"
    source_path = OUT_DIR / f"{stem}_source_data.csv"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    return svg_path, png_path, source_path


def main() -> None:
    apply_publication_style()
    data = assemble_long_table()
    source_path = OUT_DIR / "eatvul_defense_nature_source_data.csv"
    data.to_csv(source_path, index=False)
    fig = build_figure(data)
    svg_path, png_path, _ = save_outputs(fig)
    plt.close(fig)
    print(f"SVG: {svg_path}")
    print(f"PNG: {png_path}")
    print(f"Source data: {source_path}")


if __name__ == "__main__":
    main()
