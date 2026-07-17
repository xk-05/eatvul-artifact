# Evidence Boundaries of AST-Token-Only Defenses: JISA Artifact

This repository is the public reproducibility artifact for the final manuscript
**Evidence Boundaries of AST-Token-Only Defenses against EaTVul-Style Insertion
Evasion**.

The final study asks three research questions about what serialized AST-token
evidence can support, how screening behaves under matched review budgets, and
where model or deletion diagnostics stop supporting stronger deployment
claims. Its evidence supports sample-level screening and review routing. It does
not establish corrected labels, source localization, or verified automatic
sanitization.

## Final release

The canonical release is the Google Drive snapshot `JISA-Final-2026-07-17`,
materialized here as reviewable files:

- manuscript source and PDF:
  `paper_eatvul_defense_framework/latex_submission/main_jisa.tex` and
  `main_jisa.pdf`;
- generated Tables 2--9:
  `paper_eatvul_defense_framework/latex_submission/generated/`;
- Figures 1--3:
  `paper_eatvul_defense_framework/figures_submission_jisa/`;
- verified derived evidence: `results/jisa_evidence_bundle.json`,
  `results/jisa_matched_budget_summary.csv`, and
  `results/jisa_confidence_sensitivity/`;
- provenance: `manifests/jisa_final/` and
  `results/jisa_confidence_sensitivity/run_manifest.json`;
- materialization and verification code: `scripts/materialize_jisa_evidence.py`
  and `scripts/jisa_confidence_sensitivity.py`.

The final PDF is ten pages and has SHA-256
`b6fe8625b7648e9400077757e8f66762c5db7d18d44d921d6ff8a2372fb1fea7`.

## Quick verification

Use Python 3.9 or newer. The final run used the versions pinned in
`requirements_jisa.txt`.

```bash
python -m pip install -r requirements_jisa.txt
python -m pytest tests/test_jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py tests/test_artifact_checks.py -v
python scripts/jisa_confidence_sensitivity.py verify
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
```

`scripts/materialize_jisa_evidence.py` regenerates the final tables and vector
figures from the released derived evidence. PDF figure bytes may differ across
Matplotlib versions even when the rendered content is unchanged.

```bash
python scripts/materialize_jisa_evidence.py
```

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the complete workflow and
[docs/TABLE_REPRODUCTION_MAP.md](docs/TABLE_REPRODUCTION_MAP.md) for the source
of every final table and figure.

## Data boundary

This public repository intentionally does not contain `Code and Dataset.zip` or
the raw AST-token splits. Redistribution authorization for those inputs has not
been established. The release contains the derived aggregate and sample-level
evidence needed to audit the final manuscript, plus hashes and run metadata.

The excluded inputs are not required for the fast verification path. A full
retraining run of `scripts/jisa_confidence_sensitivity.py run` requires the
authorized raw splits at the local paths described in [DATA.md](DATA.md).

## Repository layout

```text
paper_eatvul_defense_framework/
  latex_submission/              final CAS TeX, PDF, bibliography, Tables 2--9
  figures_submission_jisa/       final vector Figures 1--3
results/
  jisa_evidence_bundle.json      verified multi-experiment evidence bundle
  jisa_matched_budget_summary.csv
  jisa_confidence_sensitivity/   summary, sample rows, profiles, run manifest
manifests/jisa_final/            Drive-level final release provenance
scripts/                         materialization, verification, legacy analyses
tests/                           release-boundary and evidence tests
docs/                            reviewer inventory, runbook, limitations, map
```

Older aggregate files and scripts remain for provenance and secondary
inspection. They belong to earlier manuscript iterations and are not the
canonical table map for the final JISA paper.

## Main findings represented by the release

- At a nominal 5% calibration budget, realized unattacked-review rates vary
  substantially across targets and methods.
- The target-confidence control captures 12 of 354 pooled raw adversarial
  benign predictions at that budget.
- Duplicate removal changes the pooled confidence-baseline capture among
  bypasses only modestly.
- Seven of eight deletion grids have zero median detector-output recovery;
  deletion remains a diagnostic boundary test rather than an automatic repair.

These statements are auditable through the final CSV/JSON evidence and the
generated TeX fragments checked by `scripts/check_reported_values.py`.

## Manuscript build

From `paper_eatvul_defense_framework/latex_submission/`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

The source uses the Elsevier CAS double-column class. Figures are read from
`../figures_submission_jisa/`, and generated tables are read from `generated/`.

## Responsible use

The artifact evaluates defensive screening boundaries. It does not add attack
generation prompts or claim deployable source repair. Do not reinterpret token
deletion diagnostics as source-level localization or security validation.

## Citation

Citation metadata is provided in [CITATION.cff](CITATION.cff). Until a formal
publication identifier is assigned, cite the accompanying manuscript and this
repository URL: <https://github.com/xk-05/eatvul-jisa-artifact>.
