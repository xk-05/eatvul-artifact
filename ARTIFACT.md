# Artifact Description

## Purpose

This artifact accompanies the manuscript **Detection, Not Sanitization:
Capability Boundaries of AST-token-only Defenses against EaTVul-style Code
Insertion**. It lets reviewers inspect the manuscript source, the defensive
evaluation code, table source files, selected logs where available, and the
limits of the public AST-token setting.

## Claimed Reproducibility Level

The main aggregate tables in the defense-boundary manuscript are reproducible
or auditable from the released scripts, AST-token splits, and aggregate result
files in this repository. The artifact is not a complete reproduction of every
original EaTVul attack-generation artifact or external victim-model checkpoint.

## Directory Map

- `paper_eatvul_defense_framework/latex_submission/`: manuscript source,
  bibliography, and compiled-output directories.
- `paper_eatvul_defense_framework/figures_submission/`: figures imported by the
  manuscript.
- `Code and Dataset/file/data/`: public EaTVul-style AST-token splits.
- `scripts/`: defensive experiments, wrappers, artifact checks, and manifest
  generation.
- `results/`: aggregate CSVs and selected CSV/JSON/JSONL outputs.
- `docs/`: reviewer-facing inventory, runbook, table map, and limitations.

## Requirements

Lightweight checks:

```bash
python scripts/check_artifact.py
python scripts/eatvul_reproduce.py dataset-summary
```

Full reruns:

```bash
conda env create -f environment.yml
conda activate eatvul
```

The local project was developed against a Conda environment named `eatvul`.
Neural sanity-check rows may require additional local model files and more
runtime than the smoke checks.

## Minimal Smoke Test

```bash
make smoke
```

This verifies artifact structure and prints dataset counts. It does not retrain
large neural models.

## Full Reproduction

Use the scripts listed in `docs/TABLE_REPRODUCTION_MAP.md`. Full reruns for the
gate, quarantine, F1-constrained policy, and diagnostic deletion tests are
supported from the public AST-token splits. Some rows are documented as
aggregate-file reproducible only because complete paired per-sample logs are not
available.

## Expected Outputs

- `scripts/check_artifact.py`: exits with status 0 when required files and
  result columns are present.
- `scripts/make_tables.py`: writes a lightweight summary under
  `results/tables/table_reproduction_summary.csv`.
- `scripts/make_figures.py`: verifies expected manuscript figures and writes
  `results/figures/figure_inventory.csv`.
- `scripts/build_manifest.py`: writes `artifact_manifest.json`.

## Known Limitations

Unavailable objects include true inserted spans, source diffs,
source-to-token mappings, CFGs, PDGs, compiler-validated adaptive snippets, and
complete paired prediction logs for all defense layers. These limits are
documented in `MISSING_OBJECTS.md` and `docs/LIMITATIONS_FOR_REVIEWERS.md`.
