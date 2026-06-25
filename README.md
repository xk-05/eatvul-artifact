# Detection, Not Sanitization: JISA Reproducibility Artifact

This repository is a reproducibility artifact for the manuscript
**Detection, Not Sanitization: Capability Boundaries of AST-token-only Defenses
against EaTVul-style Code Insertion**.

The artifact supports inspection of the manuscript source, bibliography,
figures, experiment scripts, aggregate result tables, selected CSV/JSON/JSONL
outputs where available, and the exact limits of reproducibility. It focuses on
defensive evaluation: review routing, quarantine, residual silent-bypass rate,
diagnostic deletion tests, public AST-token artifacts, project-coherent
calibration, and mixed-source stress settings.

## Included

- Manuscript source under `paper_eatvul_defense_framework/latex_submission/`.
- Submission figures under `paper_eatvul_defense_framework/figures_submission/`.
- Public EaTVul-style AST-token splits under `Code and Dataset/file/data/`.
- Defensive evaluation scripts under `scripts/`.
- Aggregate result tables under `results/`.
- Selected prediction or sanitized-output logs where they are present locally.
- Reviewer documentation in `ARTIFACT.md`, `REPRODUCIBILITY.md`, `DATA.md`,
  `MISSING_OBJECTS.md`, and `docs/`.

## Not Included

This repository does not provide true inserted spans, source diffs,
source-to-token mappings, CFGs, PDGs, compiler-validated adaptive snippets, or
complete paired prediction logs for all defense layers. These missing objects
are part of the paper's capability-boundary claim: whole-sample detection and
quarantine can be evaluated from AST-token sequences, while reliable
source-level sanitization requires richer program context.

This artifact does not add attack-generation prompts or new offensive
attack-generation tooling.

## Quick Start

```powershell
python scripts/check_artifact.py
python scripts/eatvul_reproduce.py dataset-summary
python scripts/build_manifest.py
```

On systems with `make`:

```bash
make check
make smoke
make tables
make figures
make manifest
```

## Environment

The lightweight artifact checks require Python 3.9+ and only the standard
library. Full experiment reruns use the local Conda environment named `eatvul`
with `numpy`, `scipy`, `scikit-learn`, `pandas`, and optional neural-model
dependencies. See `requirements.txt` and `environment.yml`.

## Reproduce Aggregate Tables

The main manuscript tables are backed by the result files listed in
`docs/TABLE_REPRODUCTION_MAP.md`. For a fast audit, run:

```powershell
python scripts/check_artifact.py
python scripts/make_tables.py
```

Representative full reruns use the original scripts, for example:

```powershell
conda run -n eatvul python scripts/eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.1
conda run -n eatvul python scripts/eatvul_quarantine_defense.py --clean-block-budget 0.1
conda run -n eatvul python scripts/eatvul_f1_constrained_defense.py --max-clean-f1-drop 0.03
```

The diagnostic deletion scripts are slower because they delete candidate
windows or components and rerun the target detector.

## Compile the Paper

From the repository root:

```powershell
$env:PYTHONUTF8='1'
python 'C:/Users/Administrator/.codex/plugins/cache/openai-bundled/latex/0.2.2/scripts/compile_latex.py' `
  'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex' `
  --compiler tectonic `
  --output-directory 'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/build_citation_bib_check' `
  --json
```

If that bundled compiler is not available, use a local LaTeX installation on
`paper_eatvul_defense_framework/latex_submission/main.tex`.

## Responsible Use

This artifact is for defensive evaluation and reproducibility. Do not use it to
generate new evasive code snippets or to attack deployed vulnerability-detection
services.

## Citation

Use `CITATION.cff` for software citation metadata. Update the DOI, URL, and
publication metadata after the JISA submission receives final identifiers.
