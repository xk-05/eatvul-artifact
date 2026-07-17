# Reproducibility Guide

## Environment

The final focused run used the exact packages in `requirements_jisa.txt`:
NumPy 1.26.4, pandas 2.3.3, scikit-learn 1.5.2, SciPy 1.17.1,
Matplotlib, and pytest 9.1.1. The checks also run on newer compatible Python
environments; the repository currently requires Python 3.9 or newer.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements_jisa.txt
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

## Fast audit from public files

```bash
python -m pytest tests/test_jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py tests/test_artifact_checks.py -v
python scripts/jisa_confidence_sensitivity.py verify
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
```

Expected outcomes are a passing test suite, `confidence sensitivity verification
passed`, `Text integrity check passed`, `Artifact check passed`, and a final
Tables 2--9 verification message.

## Materialize final evidence

```bash
python scripts/materialize_jisa_evidence.py
```

This uses the public verified bundle and CSV profiles to generate Tables 2--9
and Figures 1--3. It no longer requires raw AST-token splits for the dataset
profile. Matplotlib-generated PDF bytes can vary by library version or embedded
metadata; inspect rendered figures when comparing across environments.

## Confidence-output verification

```bash
python scripts/jisa_confidence_sensitivity.py verify
```

The verifier checks hashes from the confidence run manifest and recomputes the
20 summary rows from the 2,500 released sample-budget rows.

Running the experiment instead of verifying stored outputs requires authorized
raw splits under the paths in `DATA.md`:

```bash
python scripts/jisa_confidence_sensitivity.py run
```

## Manuscript build

The canonical source is
`paper_eatvul_defense_framework/latex_submission/main_jisa.tex`.

```bash
cd paper_eatvul_defense_framework/latex_submission
latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

The authorized final output is ten pages. Figures are loaded from
`../figures_submission_jisa/`; tables are loaded from `generated/`.

## Provenance

`manifests/jisa_final/FINAL_RUN_MANIFEST.json` records the final source hashes,
ten-page build, validation status, and publication boundary.
`manifests/jisa_final/confidence_run_manifest.json` records seed 7, the five
budgets, four targets, package versions, runtime, and output hashes.

Legacy scripts and aggregate files remain available for historical inspection,
but the final paper's authoritative table map is
`docs/TABLE_REPRODUCTION_MAP.md`.
