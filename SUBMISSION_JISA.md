# JISA / Elsevier Submission Wrapper

This file records the clean submission-facing entry points for the manuscript
and artifact. It does not claim that the manuscript has been converted to an
Elsevier `elsarticle` template; the current source keeps the inherited
USENIX-style filename for continuity and provides a neutral wrapper.

## Manuscript Source

- Canonical TeX source:
  `paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex`
- Compatibility wrapper:
  `paper_eatvul_defense_framework/latex_submission/main.tex`
- Expected generated PDF:
  `paper_eatvul_defense_framework/latex_submission/build_jisa_sync_check/main_usenix_style_round3_clean.pdf`

Bundled Tectonic build command used for local verification:

```powershell
$env:PYTHONUTF8 = '1'
python 'C:/Users/Administrator/.codex/plugins/cache/openai-bundled/latex/0.2.3/scripts/compile_latex.py' `
  'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex' `
  --compiler tectonic `
  --output-directory 'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/build_jisa_sync_check' `
  --json
```

If a full TeX Live environment with `latexmk` is available, the neutral wrapper
can also be built from the submission directory:

```bash
cd paper_eatvul_defense_framework/latex_submission
latexmk -xelatex -interaction=nonstopmode main.tex
```

## Submission Package Checklist

- Manuscript PDF.
- `highlights.md`.
- Data availability statement in the manuscript.
- CRediT authorship contribution statement in the manuscript.
- Declaration of competing interest in the manuscript.
- Funding statement in the manuscript.
- Artifact/repository URL: `https://github.com/xk-05/eatvul-jisa-artifact`.
- Artifact documentation: `README.md`, `ARTIFACT.md`, `DATA.md`,
  `THIRD_PARTY_DATA.md`, `docs/TABLE_REPRODUCTION_MAP.md`.

## JISA Framing Reminder

This is a security deployment and capability-boundary paper, not a generic ML
classifier paper. The supported deployment endpoint is detection plus
quarantine/review routing under project-coherent calibration. Hard override is
an upper-bound diagnostic. The evaluated token-only deletion tests did not
provide sufficient evidence for reliable source-level sanitization, and they do
not validate deployable source repair under AST-token-only evidence. CodeBERT is
used only as a bounded model-coverage sanity check, while adaptive robustness
remains a limitation and future-work item.

## Artifact Verification Commands

Run from the repository root:

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
python scripts/check_reported_values.py
python scripts/export_gate_feature_importance.py
python scripts/eatvul_reproduce.py dataset-summary
make text-check
make check
make table-check
make verify
```

Optional hygiene checks, when available:

```bash
pytest
black --check scripts
isort --check-only scripts
```

## Reproducibility Boundary

The aggregate manuscript tables are checked against stored CSV/JSON artifacts
and the AST-token split files included under `Code and Dataset/file/data/`.
Historical archives, local helper code, model packages, cached model weights,
and source-text extension data are governed by their upstream terms and are not
covered by this artifact's MIT license. True inserted spans, source diffs, CFGs,
PDGs, and parser-validated source contexts remain unavailable in the current
public AST-token-only artifact.
