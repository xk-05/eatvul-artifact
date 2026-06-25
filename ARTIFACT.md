# Artifact Description

## Purpose

This artifact accompanies the manuscript **Detection, Not Sanitization:
Capability Boundaries of AST-token-only Defenses against EaTVul-style Code
Insertion**. It lets reviewers inspect the manuscript source, the defensive
evaluation code, table source files, selected logs where available, and the
limits of the public AST-token setting.

## Claimed Reproducibility Level

The main aggregate tables in the defense-boundary manuscript are auditable from
the released scripts and aggregate result files in this repository. Dataset-size
checks, Table 6 feature-importance recomputation, and full experiment reruns
also require locally prepared EaTVul-style AST-token split files under
`Code and Dataset/file/data/`. Those split files are not redistributed through
public Git tracking because their redistribution terms are not confirmed in
this package. The artifact is not a complete reproduction of every original
EaTVul attack-generation artifact or external victim-model checkpoint.

## Directory Map

- `paper_eatvul_defense_framework/latex_submission/`: manuscript source,
  bibliography, and compiled-output directories.
- `paper_eatvul_defense_framework/figures_submission/`: figures imported by the
  manuscript.
- `data/README.md`: preparation notes for external AST-token resources.
- `Code and Dataset/file/data/`: local-only external AST-token split location
  for users who prepare the data under upstream terms.
- `scripts/`: defensive experiments, wrappers, artifact checks, and manifest
  generation.
- `results/`: aggregate CSVs and selected CSV/JSON/JSONL outputs.
- `docs/`: reviewer-facing inventory, runbook, table map, and limitations.
- `THIRD_PARTY_DATA.md`: inventory of bundled or referenced third-party data,
  archives, pretrained weights, checkpoints, and redistribution status.

## Requirements

Lightweight checks:

```bash
python scripts/check_text_integrity.py
python -m compileall scripts
python scripts/check_artifact.py
python scripts/check_reported_values.py
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

This verifies artifact structure and, when local external AST-token split files
are present, prints dataset counts. It does not retrain large neural models.

## Full Reproduction

Use the scripts listed in `docs/TABLE_REPRODUCTION_MAP.md`. Full reruns for the
gate, quarantine, F1-constrained policy, and diagnostic deletion tests require
locally prepared AST-token splits. Some rows are documented as aggregate-file
reproducible only because complete paired per-sample logs are not available.

## Expected Outputs

- `scripts/check_text_integrity.py`: exits with status 0 when tracked text
  files have real line breaks, tracked Python parses, result CSV/JSON files
  parse, and core docs/configs are readable.
- `scripts/check_artifact.py`: exits with status 0 when required files and
  result columns are present.
- `scripts/check_reported_values.py`: exits with status 0 when the reported
  aggregate table values match result CSVs within `1e-3`.
- `scripts/export_gate_feature_importance.py`: writes
  `results/eatvul_defense/gate_feature_family_importance.csv` for Table 6
  provenance and warns if it differs from the manuscript row.
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
