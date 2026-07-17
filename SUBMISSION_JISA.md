# JISA / Elsevier Submission Package

## Canonical submission files

- TeX: `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`
- PDF: `paper_eatvul_defense_framework/latex_submission/main_jisa.pdf`
- bibliography: `paper_eatvul_defense_framework/latex_submission/references.bib`
- generated Tables 2--9:
  `paper_eatvul_defense_framework/latex_submission/generated/`
- Figures 1--3: `paper_eatvul_defense_framework/figures_submission_jisa/`
- highlights: `paper_eatvul_defense_framework/latex_submission/highlights.txt`
- cover letter: `paper_eatvul_defense_framework/latex_submission/cover_letter_jisa.txt`
- declarations draft:
  `paper_eatvul_defense_framework/latex_submission/elsevier_declarations_draft.txt`

The manuscript uses the Elsevier CAS double-column template and compiles to ten
pages.

```bash
cd paper_eatvul_defense_framework/latex_submission
latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

## Submission framing

The paper is an evidence-boundary and security-deployment study. Serialized
AST-token evidence supports screening and review routing, but not label
correction, source localization, or verified automatic sanitization. Hard
override and fixed token deletion remain diagnostic analyses.

## Artifact checklist

- final manuscript PDF and editable CAS sources;
- final vector figures and generated Tables 2--9;
- derived evidence bundle, confidence sample rows, and run manifests;
- public verification and materialization scripts;
- explicit exclusion of `Code and Dataset.zip` and raw AST-token splits;
- repository URL: <https://github.com/xk-05/eatvul-jisa-artifact>.

Before submission, run:

```bash
python -m pytest -v
python scripts/jisa_confidence_sensitivity.py verify
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
```

Author identity, department, postal address, ORCID, funding, competing-interest
status, CRediT roles, and corresponding-author contact details remain items for
the author and submission system to confirm.
