# Final JISA Artifact Runbook

Run commands from the repository root unless a step says otherwise.

## 1. Install the focused environment

```bash
python -m pip install -r requirements_jisa.txt
```

## 2. Validate the public release

```bash
python -m pytest -v
python -m compileall scripts
python scripts/check_text_integrity.py
python scripts/check_artifact.py
python scripts/check_reported_values.py
python scripts/jisa_confidence_sensitivity.py verify
```

## 3. Regenerate derived paper objects

```bash
python scripts/materialize_jisa_evidence.py
```

The script consumes the verified public bundle, matched-budget summary, and
token-length profile. It writes Tables 2--9 and Figures 1--3. It does not need
raw splits for materialization. Restore or compare the authorized Drive PDFs
after a cross-environment run because Matplotlib PDF bytes may vary.

## 4. Build the manuscript

```bash
cd paper_eatvul_defense_framework/latex_submission
latexmk -pdf -interaction=nonstopmode -halt-on-error main_jisa.tex
```

Expected: a ten-page PDF with no undefined citations or references.

## 5. Optional full confidence rerun

Only run this with authorized raw AST-token splits prepared as documented in
`DATA.md`:

```bash
python scripts/jisa_confidence_sensitivity.py run
```

The public audit uses `verify`, not `run`.

## 6. Refresh repository provenance

```bash
python scripts/build_manifest.py
git diff --check
git status --short
```

Review the change for raw data, archives, credentials, caches, local paths, and
unexpected generated differences before committing.
