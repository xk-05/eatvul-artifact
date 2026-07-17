# JISA LaTeX submission package

This directory contains the canonical manuscript formatted with Elsevier's
CAS double-column template.

## Build

From this directory, run:

```bash
TEXMFVAR=/tmp/texmf-var latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

The compiled manuscript is `main_jisa.pdf`. Figures are read from
`../figures_submission_jisa/`, and generated tables are in `generated/`.

## Submission files

- `main_jisa.tex`: editable manuscript source.
- `references.bib`: bibliography database.
- `cas-dc.cls`, `cas-common.sty`, `cas-model2-names.bst`: Elsevier CAS files.
- `highlights.txt`: four highlights, each at most 85 characters.
- `cover_letter_jisa.txt`: draft cover letter.
- `elsevier_declarations_draft.txt`: declarations requiring author confirmation.

## Reproducibility boundary

The derived artifact verifies the newly executed target-confidence experiment
from sample-level outputs. The larger fixed-grid results are represented by a
hash-verified evidence bundle because the received source backup does not
contain all historical raw output files. Raw AST-token inputs are intentionally
excluded because redistribution authorization has not been established.

Before submission, the author must add a permanent repository identifier for
the redistributable derived artifact and verify the complete affiliation,
funding, competing-interest, and authorship metadata.
