# JISA revision and verification notes

## Main revision

The manuscript was reframed around an explicit evidence-to-action boundary:
serialized AST-token artifacts support screening and review routing, but do not
support claims of corrected labels, source localization, or verified automatic
sanitization. The paper now uses the Elsevier CAS double-column template and
contains a title page, abstract, six keywords, CRediT statement, competing
interest statement, funding statement, AI-assistance declaration, and data
availability statement.

## Newly executed control

`scripts/jisa_confidence_sensitivity.py` retrains a TF--IDF logistic-regression
target detector for each target, holds out 20% of the official training split
for clean calibration, and evaluates the untouched official unattacked and
adversarial tests. A deterministic exact-k policy resolves threshold ties.

At the nominal 5% budget, the control captures 12 of 354 raw adversarial
benign predictions. Removing the 47 cross-dataset duplicate attack rows changes
pooled capture among bypasses from 3.39% to 2.82--3.11%. All values are written
to sample-level CSVs and can be recomputed with the verifier.

## Verification commands

```bash
.venv/bin/python -m pytest tests/test_jisa_confidence_sensitivity.py tests/test_materialize_jisa_evidence.py -v
.venv/bin/python scripts/jisa_confidence_sensitivity.py verify
.venv/bin/python scripts/materialize_jisa_evidence.py
cd paper_eatvul_defense_framework/latex_submission
TEXMFVAR=/tmp/texmf-var latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

The focused test suite passes 4/4 tests, the confidence verifier passes, and
the final manuscript compiles to ten pages without undefined citations or
references.

## Known submission actions

1. Deposit the redistributable derived artifact and insert its DOI or permanent
   repository URL in the manuscript and submission system.
2. Confirm the author's department, postal address, ORCID (if any), funding,
   competing-interest declaration, and CRediT roles.
3. Obtain redistribution authorization before publishing any raw AST-token
   splits; otherwise retain the documented access limitation.
4. The received full-backup archive is incomplete because part `.010` is
   missing. The derived evidence bundle is verified, but missing historical raw
   outputs cannot be recreated from that incomplete backup alone.
