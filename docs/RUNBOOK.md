# Reviewer Runbook

## 0. Check Text Integrity and Python Syntax

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
```

Expected: exit code 0. The text-integrity check should end with
`Text integrity check passed`, and compileall should not report syntax errors.

## 1. Check Artifact Structure

```bash
python scripts/check_artifact.py
```

Expected: exit code 0 and a summary ending with `Artifact check passed`.

Then verify that manuscript-reported aggregate values match the result CSVs:

```bash
python scripts/check_reported_values.py
```

Expected: exit code 0 and a summary beginning with
`Reported-value check passed`.

## 2. Verify Dataset Counts

```bash
python scripts/eatvul_reproduce.py dataset-summary
```

Expected counts:

- ASTERISK: 880 train, 367 test, 50 adv
- OPENSSL: 520 train, 213 test, 50 adv
- CWE119: 5670 train, 2451 test, 200 adv
- CWE399: 545 train, 255 test, 200 adv

## 3. Rebuild Lightweight Table Inventory

```bash
python scripts/make_tables.py
```

Expected output:

```text
results/tables/table_reproduction_summary.csv
```

## 3b. Export Table 6 Feature-family Provenance

```bash
python scripts/export_gate_feature_importance.py
```

Expected output:

```text
results/eatvul_defense/gate_feature_family_importance.csv
```

If the recomputed LODO average differs from the stored provenance CSV, the
script prints a warning; do not silently edit manuscript values.

## 4. Rebuild Lightweight Figure Inventory

```bash
python scripts/make_figures.py
```

Expected output:

```text
results/figures/figure_inventory.csv
```

## 5. Generate Manifest

```bash
python scripts/build_manifest.py
```

Expected output:

```text
artifact_manifest.json
```

## 6. Optional Full Reruns

Full reruns require the `eatvul` Conda environment:

```bash
conda run -n eatvul python scripts/eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.1
conda run -n eatvul python scripts/eatvul_quarantine_defense.py --clean-block-budget 0.1
conda run -n eatvul python scripts/eatvul_f1_constrained_defense.py --max-clean-f1-drop 0.03
```

Diagnostic deletion reruns are slower:

```bash
conda run -n eatvul python scripts/eatvul_localize_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-window-fpr 0.01 --window 1536 --stride 768 --max-spans 2 --candidate-windows 32 --min-prob-gain 0.005 --gate-on-benign
conda run -n eatvul python scripts/eatvul_component_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-component-fpr 0.01 --max-cluster 3 --max-spans 1 --candidate-components 16 --min-prob-gain 0.001 --gate-on-benign --calibration-items 200
```

The fixed-window Table 9/Table 15 row uses `min_prob_gain = 0.005`; the
component Table 9/Table 15 row uses `min_prob_gain = 0.001`. Use the sidecar
configuration JSONs beside the reported CSVs to audit the exact settings.

## 7. Compile Manuscript

Use the bundled Tectonic helper or local LaTeX. If neither is available, inspect
the source and compiled PDF already present in the build directory.
