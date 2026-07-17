# Final JISA Artifact Inventory

## Manuscript package

- `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`
- `paper_eatvul_defense_framework/latex_submission/main_jisa.pdf`
- `paper_eatvul_defense_framework/latex_submission/references.bib`
- Elsevier CAS class/style/bibliography files and thumbnail assets
- `paper_eatvul_defense_framework/latex_submission/generated/jisa_*.tex`
- cover letter, highlights, declaration draft, and submission README
- `paper_eatvul_defense_framework/figures_submission_jisa/*.pdf`

## Derived evidence

- `results/jisa_evidence_bundle.json`: verified multi-experiment bundle.
- `results/jisa_matched_budget_summary.csv`: 100 matched-budget rows.
- `results/jisa_confidence_sensitivity/confidence_adv_samples.csv`: 2,500
  sample-budget rows.
- `results/jisa_confidence_sensitivity/confidence_summary.csv`: 20 summary
  rows.
- `results/jisa_confidence_sensitivity/duplicate_sensitivity.csv`: 15 control
  rows.
- `results/jisa_confidence_sensitivity/token_length_profile.csv`: 12 role rows.

## Provenance and software

- `manifests/jisa_final/FINAL_RUN_MANIFEST.json`
- `manifests/jisa_final/confidence_run_manifest.json`
- `results/jisa_confidence_sensitivity/run_manifest.json`
- `requirements_jisa.txt`
- `scripts/materialize_jisa_evidence.py`
- `scripts/jisa_confidence_sensitivity.py`
- focused tests under `tests/test_jisa_*.py` and
  `tests/test_materialize_jisa_evidence.py`

## Exclusions

`Code and Dataset.zip`, raw AST-token splits, model caches, credentials, and
temporary build outputs are not tracked. Historical scripts/results retained in
other directories are auxiliary provenance, not the final manuscript table map.
