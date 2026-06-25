# Reproducibility Guide

## What Can Be Reproduced

The main numerical claims in the AST-token defense-boundary manuscript can be
audited from the tracked files in this repository where aggregate result CSVs
are available. Dataset-size checks, Table 6 feature-importance recomputation,
and full experiment reruns require locally prepared external AST-token split
files under `Code and Dataset/file/data/`:

- dataset sizes for ASTERISK, OPENSSL, CWE119, and CWE399;
- sample-level gate results under hard override;
- aggregate-count uncertainty checks;
- feature-family contribution summary;
- anomaly-baseline comparison;
- bounded CodeBERT/BiLSTM sanity-check rows where result files are present;
- fixed-window diagnostic deletion rows;
- AST-token component diagnostic deletion rows;
- quarantine and F1-constrained deployment-policy rows.

## What Is Aggregate-File Reproducible

Some tables are reproduced from aggregate CSVs because complete paired
prediction logs are not available for every defense layer. This is intentional
and documented in the manuscript.

## Smoke Commands

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
python scripts/check_reported_values.py
```

After preparing the external AST-token split files locally, also run:

```bash
python scripts/eatvul_reproduce.py dataset-summary
```

The original experiment environment did not fully lock exact historical package
versions. This release therefore records a Python 3.9 Conda environment with
bounded dependency ranges in `environment.yml` and `requirements.txt`.

## Representative Rerun Commands

Prepare the external AST-token split files described in `DATA.md` before
running the representative full-rerun commands below.

```bash
conda run -n eatvul python scripts/eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.1
conda run -n eatvul python scripts/eatvul_anomaly_baselines.py
conda run -n eatvul python scripts/eatvul_quarantine_defense.py --clean-block-budget 0.1
conda run -n eatvul python scripts/eatvul_f1_constrained_defense.py --max-clean-f1-drop 0.03
conda run -n eatvul python scripts/eatvul_localize_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-window-fpr 0.01 --window 1536 --stride 768 --max-spans 2 --candidate-windows 32 --min-prob-gain 0.005 --gate-on-benign
conda run -n eatvul python scripts/eatvul_component_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-component-fpr 0.01 --max-cluster 3 --max-spans 1 --candidate-components 16 --min-prob-gain 0.001 --gate-on-benign --calibration-items 200
conda run -n eatvul python scripts/export_gate_feature_importance.py
```

For the diagnostic deletion rows, the reported fixed-window setting uses
`min_prob_gain = 0.005`, while the reported AST-token component setting uses
`min_prob_gain = 0.001`. The sidecar config JSONs in the corresponding
`results/` directories record these values.

## Paper Compilation

The canonical source is:

```text
paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex
```

The compatibility entry point is:

```text
paper_eatvul_defense_framework/latex_submission/main.tex
```

Compile with the bundled Tectonic helper when available, or use a local LaTeX
installation.
