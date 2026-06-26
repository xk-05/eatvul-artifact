# Detection, Not Sanitization: JISA Reproducibility Artifact

This repository is the reproducibility artifact for the manuscript
**Detection, Not Sanitization: Capability Boundaries of AST-token-only Defenses
against EaTVul-style Code Insertion**.

The artifact supports inspection and reproduction of the defense-boundary study:
manuscript source, bibliography, figures, experiment scripts, aggregate result
tables, selected CSV/JSON/JSONL outputs where available, configurations,
calibrated thresholds, and the exact limits of reproducibility. The evaluation
focuses on defensive behavior: review routing, quarantine, residual
silent-bypass rate, diagnostic deletion tests, public AST-token artifacts,
project-coherent calibration, and mixed-source stress settings.

This artifact does **not** claim reliable automatic sanitization. The paper's
central claim is that AST-token-only evidence can support suspicious benign
prediction detection and quarantine in some settings, but it is insufficient for
verified source-level repair without richer program context.

## Table of Contents

1. [Artifact Scope](#artifact-scope)
2. [Repository Layout](#repository-layout)
3. [What Can and Cannot Be Reproduced](#what-can-and-cannot-be-reproduced)
4. [Environment Setup](#environment-setup)
5. [Quick Reproduction Path](#quick-reproduction-path)
6. [Step-by-step Reproduction Guide](#step-by-step-reproduction-guide)
7. [Main Table Reproduction Map](#main-table-reproduction-map)
8. [Full Experiment Reruns](#full-experiment-reruns)
9. [Paper Compilation](#paper-compilation)
10. [Expected Outputs](#expected-outputs)
11. [Troubleshooting](#troubleshooting)
12. [Responsible Use](#responsible-use)
13. [Citation](#citation)

## Artifact Scope

This repository includes:

- manuscript source under `paper_eatvul_defense_framework/latex_submission/`;
- bibliography under `paper_eatvul_defense_framework/latex_submission/references.bib`;
- submission figures under `paper_eatvul_defense_framework/figures_submission/`;
- aggregate result tables under `results/`, with external EaTVul-style
  AST-token splits prepared locally under `Code and Dataset/file/data/` only
  when needed for full reruns;
- defensive evaluation scripts under `scripts/`;
- selected prediction or sanitized-output logs where available;
- reviewer documentation in `ARTIFACT.md`, `REPRODUCIBILITY.md`, `DATA.md`,
  `MISSING_OBJECTS.md`, `THIRD_PARTY_DATA.md`, and `docs/`;
- a lightweight artifact validator in `scripts/check_artifact.py`;
- a text/newline and parseability validator in `scripts/check_text_integrity.py`;
- a reported-value checker in `scripts/check_reported_values.py`;
- a Table 6 feature-family export script in
  `scripts/export_gate_feature_importance.py`;
- a SHA256 manifest generator in `scripts/build_manifest.py`.

This repository does not add attack-generation prompts or new offensive
attack-generation tools.

## Repository Layout

```text
.
|-- README.md
|-- ARTIFACT.md
|-- REPRODUCIBILITY.md
|-- DATA.md
|-- MISSING_OBJECTS.md
|-- CITATION.cff
|-- requirements.txt
|-- environment.yml
|-- Makefile
|-- data/
|   `-- README.md
|-- configs/
|   |-- gate/
|   |-- anomaly_baselines/
|   |-- diagnostic_deletion/
|   `-- deployment_policies/
|-- docs/
|   |-- ARTIFACT_INVENTORY.md
|   |-- TABLE_REPRODUCTION_MAP.md
|   |-- RUNBOOK.md
|   `-- LIMITATIONS_FOR_REVIEWERS.md
|-- paper_eatvul_defense_framework/
|   |-- figures_submission/
|   `-- latex_submission/
|-- results/
|   |-- eatvul_defense/
|   |-- eatvul_anomaly_baselines/
|   |-- neural_target_gate/
|   |-- eatvul_local_defense/
|   |-- eatvul_component_defense/
|   |-- eatvul_quarantine_defense/
|   |-- eatvul_f1_constrained_defense/
|   |-- tables/
|   `-- figures/
`-- scripts/
```

## What Can and Cannot Be Reproduced

### Reproducible or auditable from this repository

- Dataset sizes for ASTERISK, OPENSSL, CWE119, and CWE399.
- RQ1 sample-level gate under hard override.
- RQ2 anomaly-baseline comparison.
- RQ3 bounded neural target sanity-check rows from existing aggregate files.
- RQ4 fixed-window diagnostic deletion rows.
- RQ5 AST-token component diagnostic deletion rows.
- RQ6 quarantine policy and F1-constrained hard override.
- The table and figure inventories used by the review artifact.

### Not fully reproducible from current files

The following objects are unavailable and are explicitly documented in
`MISSING_OBJECTS.md`:

- true inserted spans;
- source diffs;
- source-to-token mappings;
- CFGs;
- PDGs;
- compiler-validated adaptive snippets;
- complete paired prediction logs for all defense layers.

These missing objects are not incidental. They are part of the capability
boundary studied in the paper. Whole-sample detection and quarantine can be
evaluated from AST-token sequences, but reliable source-level sanitization
requires richer source and program-analysis evidence.

## Environment Setup

### Lightweight artifact checks

Use Python 3.9 or newer. The structure and text-integrity checks are lightweight;
the reported-value checks and CSV smoke tests use `pandas`, which is included in
`requirements.txt` and `environment.yml`.

```bash
python --version
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
```

Expected final line:

```text
Artifact check passed
```

### Full experiment environment

The original local reruns used a Conda environment named `eatvul`. The supplied
`environment.yml` records the release environment. Exact historical package
versions were not fully locked in the original experiment logs; this artifact
therefore uses bounded dependencies for reproducible checks and reruns:

```bash
conda env create -f environment.yml
conda activate eatvul
```

If the environment already exists:

```bash
conda run -n eatvul python --version
```

The fast artifact checks do not require this environment. Full gate, anomaly,
deployment-policy, and diagnostic-deletion reruns do.

## Quick Reproduction Path

Use this path first. It verifies that the artifact is complete, the expected
dataset splits are present, and the aggregate result files needed by the
manuscript exist with the expected columns.

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
python scripts/check_reported_values.py
python scripts/eatvul_reproduce.py dataset-summary
python scripts/export_gate_feature_importance.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/build_manifest.py
```

On systems with `make`:

```bash
make text-check
make check
make table-check
make verify
make tables
make figures
make manifest
```

Note for Windows PowerShell users: if `make` is not installed, run the Python
commands above directly. They are equivalent to the lightweight Makefile
targets.

## Step-by-step Reproduction Guide

### Step 1: Validate text integrity and Python syntax

Command:

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
```

What this checks:

- tracked text files use LF line endings without CR bytes;
- tracked Python files parse with `ast.parse`;
- tracked result CSV files can be parsed and have data rows;
- result JSON files parse as JSON;
- `requirements.txt`, `environment.yml`, `Makefile`, TeX wrappers, and core
  documentation have normal multiline structure.

Expected final line:

```text
Text integrity check passed
```

### Step 1b: Validate the artifact package

Command:

```bash
python scripts/check_artifact.py
```

What this checks:

- required documentation files exist;
- required manuscript files exist;
- required result CSV files exist;
- result CSV files contain expected columns;
- AST-token dataset split counts match the manuscript when local external split
  files are present;
- missing objects are explicitly documented;
- tracked files do not look like obvious secrets.

Expected output:

```text
Required files: 22 OK
Result files: 7 OK
Config sidecars: 2 OK
Dataset split counts: 4 OK
Missing-object documentation: OK
Tracked-file hygiene: OK
Artifact check passed
```

If the external AST-token split files have not been prepared locally, the
dataset line is instead:

```text
Dataset split counts: external AST-token splits not bundled; see DATA.md
```

### Step 1c: Check manuscript-reported aggregate values

Command:

```bash
python scripts/check_reported_values.py
```

What this checks:

- Table 4 sample-level gate values;
- Table 6 gate feature-family LODO-average values;
- Table 7 anomaly-baseline values;
- Table 8 CodeBERT bounded sanity-check values;
- Table 9 diagnostic deletion values;
- Table 10 quarantine values;
- Table 11 F1-constrained hard-override values;
- Table 15 token-modification proxy values.

The checker reads existing aggregate CSV files and fails with the source file,
dataset, method, column, expected value, and actual value if any reported value
differs by more than `1e-3`.

### Step 2: Verify locally prepared AST-token split sizes

Command:

```bash
python scripts/eatvul_reproduce.py dataset-summary
```

The public Git repository does not redistribute the external AST-token split
files. If they have not been prepared locally, this command prints an
external-data notice and exits without changing result files. If the files are
present under `Code and Dataset/file/data/`, expected output is:

```text
dataset,split,total,label_0,label_1
asterisk,train,880,810,70
asterisk,test,367,347,20
asterisk,adv,50,0,50
openssl,train,520,400,120
openssl,test,213,176,37
openssl,adv,50,0,50
cwe119,train,5670,3500,2170
cwe119,test,2451,1518,933
cwe119,adv,200,0,200
cwe399,train,545,330,215
cwe399,test,255,157,98
cwe399,adv,200,0,200
```

This verifies the dataset-size evidence used in the manuscript for a prepared
local copy.

### Step 3: Rebuild the table inventory

Command:

```bash
python scripts/make_tables.py
```

Expected output file:

```text
results/tables/table_reproduction_summary.csv
```

This file records which aggregate CSVs back the main manuscript tables and how
many rows each source file contains.

### Step 3b: Export Table 6 feature-family provenance

Command:

```bash
python scripts/export_gate_feature_importance.py
```

Expected output file:

```text
results/eatvul_defense/gate_feature_family_importance.csv
```

This script retrains the leave-one-dataset-out random-forest gate using the same
feature extraction path as `scripts/eatvul_defense.py`, groups selected scalar
feature importances into rare-token, unseen-token, bigram-NLL, and AST-structure
families, and normalizes those four families to 100%. If the recomputed LODO
average differs from the manuscript Table 6 row, the script writes the CSV and
prints a warning rather than changing the manuscript silently.

### Step 4: Rebuild the figure inventory

Command:

```bash
python scripts/make_figures.py
```

Expected output file:

```text
results/figures/figure_inventory.csv
```

This step verifies that all expected manuscript figure assets are present under
`paper_eatvul_defense_framework/figures_submission/`.

### Step 5: Build a checksum manifest

Command:

```bash
python scripts/build_manifest.py
```

Expected output file:

```text
artifact_manifest.json
```

The manifest records SHA256 checksums for tracked manuscript, documentation,
script, figure, result, and configuration files. It intentionally excludes
license-unclear external AST-token splits and local model/checkpoint artifacts.
Pre-removal checksums for the external split files are recorded in
`THIRD_PARTY_DATA.md`.

### Step 6: Inspect the detailed table map

Open:

```text
docs/TABLE_REPRODUCTION_MAP.md
```

This file maps each manuscript table or figure to its source script, source data
or result file, output file, reproducibility level, and limitations.

## Main Table Reproduction Map

The most important aggregate sources are:

| Manuscript item | Main source file |
| --- | --- |
| Table 2: dataset sizes | local external `Code and Dataset/file/data/*_ast_*.json`; checksums in `THIRD_PARTY_DATA.md` |
| Table 4: sample-level gate | `results/eatvul_defense/lodo_calib_fpr_0.1_results.csv` |
| Table 5: aggregate-count uncertainty checks | `results/eatvul_defense/lodo_calib_fpr_0.1_results.csv` |
| Table 6: gate feature-family contribution | `results/eatvul_defense/gate_feature_family_importance.csv` |
| Table 7: anomaly baselines | `results/eatvul_anomaly_baselines/anomaly_baseline_results.csv` |
| Table 8: neural sanity check | `results/neural_target_gate/neural_target_gate_results.csv` |
| Table 9: fixed-window deletion | `results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv` |
| Table 9: component deletion | `results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv` |
| Table 10: quarantine policy | `results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv` |
| Table 11: F1-constrained policy | `results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv` |

For the complete mapping, see `docs/TABLE_REPRODUCTION_MAP.md`.

## Full Experiment Reruns

The following commands recompute the main aggregate result files from locally
prepared AST-token splits. They can take longer than the lightweight artifact
checks because they train target models, train gates, delete candidate token
regions, and rerun target detectors. Prepare the external data as described in
`DATA.md` before running them.

### RQ1: Sample-level gate under hard override

Command:

```bash
conda run -n eatvul python scripts/eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.1
```

Expected output file:

```text
results/eatvul_defense/lodo_calib_fpr_0.1_results.csv
```

Representative expected OPENSSL row values:

- `target_clean_f1`: approximately `0.829`
- `defended_clean_f1`: approximately `0.693`
- `baseline_asr`: `0.760`
- `defended_asr`: `0.120`
- `asr_reduction`: `0.640`

### RQ2: Classic anomaly baselines

Command:

```bash
conda run -n eatvul python scripts/eatvul_anomaly_baselines.py
```

Expected output file:

```text
results/eatvul_anomaly_baselines/anomaly_baseline_results.csv
```

This compares the supervised gate with Isolation Forest, One-Class SVM, Local
Outlier Factor, and Mahalanobis baselines under the same clean-FPR calibration.

### RQ3: Bounded neural sanity check

Command:

```bash
conda run -n eatvul python scripts/eatvul_neural_target_gate.py
```

Expected output file:

```text
results/neural_target_gate/neural_target_gate_results.csv
```

This step is more expensive and may require local neural-model dependencies and
model files. The stored aggregate CSV is included for auditability. The neural
rows are a bounded sanity check, not broad neural-model evidence.

### RQ4: Fixed-window diagnostic deletion

Command:

```bash
conda run -n eatvul python scripts/eatvul_localize_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-window-fpr 0.01 --window 1536 --stride 768 --max-spans 2 --candidate-windows 32 --min-prob-gain 0.005 --gate-on-benign
```

Expected output file:

```text
results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv
```

Configuration sidecar:

```text
results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_config.json
```

This is a diagnostic deletion test. It deletes suspicious AST-token windows and
reruns the target detector. It is not a verified source-level sanitizer.

### RQ5: AST-token component diagnostic deletion

Command:

```bash
conda run -n eatvul python scripts/eatvul_component_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-component-fpr 0.01 --max-cluster 3 --max-spans 1 --candidate-components 16 --min-prob-gain 0.001 --gate-on-benign --calibration-items 200
```

Expected output file:

```text
results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv
```

Configuration sidecar:

```text
results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_config.json
```

This is also a diagnostic boundary test. It uses approximate AST-token
components, not source spans, CFG regions, or PDG slices.

The reported fixed-window setting uses `min_prob_gain = 0.005`; the reported
AST-token component setting uses `min_prob_gain = 0.001`. The component script's
default may differ from the reported command, so use the command and sidecar
above when reproducing Table 9 and Table 15.

### RQ6: Quarantine policy

Command:

```bash
conda run -n eatvul python scripts/eatvul_quarantine_defense.py --clean-block-budget 0.1
```

Expected output file:

```text
results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv
```

Quarantine means review routing. Quarantined adversarial samples are not counted
as corrected vulnerable predictions. The security metric is residual
silent-bypass rate.

### RQ6: F1-constrained hard override

Command:

```bash
conda run -n eatvul python scripts/eatvul_f1_constrained_defense.py --max-clean-f1-drop 0.03
```

Expected output file:

```text
results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv
```

This is a utility-constrained diagnostic override policy, not the deployment
recommendation.

## Paper Compilation

The canonical manuscript source is:

```text
paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex
```

The compatibility entry point is:

```text
paper_eatvul_defense_framework/latex_submission/main.tex
```

### Using the bundled Tectonic helper

From the repository root on the original local setup:

```powershell
$env:PYTHONUTF8='1'
python 'C:/Users/Administrator/.codex/plugins/cache/openai-bundled/latex/0.2.3/scripts/compile_latex.py' `
  'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex' `
  --compiler tectonic `
  --output-directory 'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/build_artifact_check' `
  --json
```

Expected result:

```text
paper_eatvul_defense_framework/latex_submission/build_artifact_check/main_usenix_style_round3_clean.pdf
```

### Using a local LaTeX installation

If you have Tectonic:

```bash
cd paper_eatvul_defense_framework/latex_submission
tectonic main.tex
```

If you have TeX Live with `latexmk`:

```bash
cd paper_eatvul_defense_framework/latex_submission
latexmk -pdf -xelatex main.tex
```

The repository also contains an audited compiled PDF at:

```text
paper_eatvul_defense_framework/latex_submission/build_citation_bib_check/main_usenix_style_round3_clean.pdf
```

## Expected Outputs

After the quick reproduction path, these files should exist:

```text
artifact_manifest.json
results/eatvul_defense/gate_feature_family_importance.csv
results/tables/table_reproduction_summary.csv
results/figures/figure_inventory.csv
```

The artifact check should end with:

```text
Artifact check passed
```

The text-integrity check should end with:

```text
Text integrity check passed
```

The reported-value check should begin with:

```text
Reported-value check passed
```

With local external data prepared, the dataset-summary command should report
the split sizes listed in
[Step 2](#step-2-verify-locally-prepared-ast-token-split-sizes). Without local
external data, it prints an external-data preparation notice.

## Troubleshooting

### `make` is not installed

Run the Python commands directly:

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
python scripts/check_reported_values.py
python scripts/export_gate_feature_importance.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/build_manifest.py
```

Run `python scripts/eatvul_reproduce.py dataset-summary` after preparing the
external AST-token split files locally.

### `conda run -n eatvul` fails

Create the environment:

```bash
conda env create -f environment.yml
```

If dependency resolution differs on your platform, install the experiment
packages manually:

```bash
pip install numpy scipy scikit-learn pandas matplotlib python-docx
```

Neural sanity-check scripts may additionally require `torch`, `transformers`,
and `tensorflow`.

### Full reruns overwrite aggregate CSVs

The experiment scripts write to their documented `results/` paths. If you want
to compare a fresh run against the stored artifact values, copy the existing CSV
first or run in a separate working tree.

### Third-party data and model permissions

See `THIRD_PARTY_DATA.md`. The MIT license covers the artifact's original code
and documentation only. Dataset archives, model archives, pretrained weights,
and cached checkpoints may require upstream permission review before public
redistribution.

### External AST-token data are missing

The public repository intentionally does not track `Code and Dataset/` because
the redistribution terms for those EaTVul-style resources are not confirmed in
this package. Use `DATA.md` and `THIRD_PARTY_DATA.md` to prepare a local copy
when running dataset-size checks, feature-importance recomputation, or full
experiment reruns.

### The diagnostic deletion rows do not show strong recovery

That is expected. The deletion methods are diagnostic boundary tests. They do
not have true inserted spans, source diffs, source-to-token mappings, CFGs, or
PDGs, so they should not be interpreted as verified source-level repair.

## Responsible Use

This artifact is for defensive evaluation and reproducibility. Do not use it to
generate new evasive code snippets or attack deployed vulnerability-detection
services. The repository does not add attack-generation prompts or new
offensive attack-generation tools.

## Citation

Use `CITATION.cff` for software citation metadata. Update DOI, URL, and
publication metadata after the JISA submission receives final identifiers.
