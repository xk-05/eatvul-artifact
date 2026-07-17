# Artifact Description

## Claim and scope

This artifact accompanies **Evidence Boundaries of AST-Token-Only Defenses
against EaTVul-Style Insertion Evasion**. It supports the final paper's three
research questions with manuscript sources, derived evidence, run provenance,
materialization code, and validation tests.

The supported operational endpoint is screening plus review routing. Hard
override and token deletion are diagnostic analyses. The artifact does not
support claims of corrected labels, source localization, compilable repair, or
security/functional validation.

## Canonical objects

- `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`: final
  Elsevier CAS source.
- `paper_eatvul_defense_framework/latex_submission/main_jisa.pdf`: authorized
  ten-page final PDF.
- `paper_eatvul_defense_framework/latex_submission/generated/`: final Tables
  2--9.
- `paper_eatvul_defense_framework/figures_submission_jisa/`: final Figures
  1--3.
- `results/jisa_evidence_bundle.json`: verified experiment evidence bundle.
- `results/jisa_matched_budget_summary.csv`: 100-row screening grid.
- `results/jisa_confidence_sensitivity/`: final confidence summaries,
  sample-level rows, duplicate sensitivity, token profiles, and run manifest.
- `manifests/jisa_final/`: final Drive release and confidence-run provenance.

## Verification levels

1. `python scripts/check_text_integrity.py` checks tracked text, Python, CSV,
   JSON, manifests, and the canonical TeX entry point.
2. `python scripts/check_artifact.py` checks required release objects, result
   schemas, budgets, targets, and tracked-file hygiene.
3. `python scripts/check_reported_values.py` verifies the exact final generated
   fragments for Tables 2--9 and their backing evidence grids.
4. `python scripts/jisa_confidence_sensitivity.py verify` recomputes confidence
   summaries from the released sample rows.
5. `python -m pytest -v` runs release-boundary, evidence, and legacy checks.

## Publication boundary

`Code and Dataset.zip` and raw AST-token splits are not published because their
redistribution authorization has not been established. The repository includes
derived evidence and hashes, not the excluded raw inputs. The incomplete
historical backup part `.010` is also documented in `JISA_REVISION_NOTES.md`.

Legacy files from prior manuscript iterations are retained where useful for
provenance. They are not canonical sources for the final table numbering.
