# Data Documentation

The main evaluation uses four public EaTVul-style AST-token datasets. Files are
JSONL-like `.json` files, one object per line, with at least `func`, `target`,
and `idx`-style fields where available.

## Dataset Summary

| Dataset | Role | Clean train | Clean test | ADV test | Local paths |
| --- | --- | ---: | ---: | ---: | --- |
| ASTERISK | Project-coherent | 880 | 367 | 50 | `Code and Dataset/file/data/asterisk_ast_*.json` |
| OPENSSL | Project-coherent | 520 | 213 | 50 | `Code and Dataset/file/data/openssl_ast_*.json` |
| CWE119 | Mixed-source stress setting | 5670 | 2451 | 200 | `Code and Dataset/file/data/cwe119_ast_*.json` |
| CWE399 | Mixed-source stress setting | 545 | 255 | 200 | `Code and Dataset/file/data/cwe399_ast_*.json` |

## Required and Optional Data

The lightweight aggregate-table audit uses the stored result CSV files under
`results/` and, for dataset-size and feature-importance checks, the AST-token
split files under `Code and Dataset/file/data/`. Full reruns of the main
TF-IDF/logistic-regression target, gate, anomaly-baseline, quarantine,
F1-constrained, and diagnostic-deletion experiments read those AST-token split
files directly.

Neural sanity-check reruns may additionally require pretrained CodeBERT or
other Hugging Face model files and local fine-tuned checkpoints. Those files are
not required for the lightweight artifact checks or for auditing the stored
aggregate CSV values.

## Redistribution Status

The AST-token files are part of a local EaTVul resource package. They are
included in this artifact to support aggregate-table checks and full reruns,
but their upstream redistribution terms are not established in this package and
they are not covered by the MIT license. If the archival release cannot confirm
permission, remove these split files from the public release and provide
checksum-based preparation instructions instead.

Historical local archives (`Code and Dataset.zip`, `model.zip`), Apple metadata
files, and EaTVul helper code under `Code and Dataset/file/code/` are not part
of the tracked public release. Local copies may remain in a reviewer or author
workspace, but they are ignored to avoid implying that license-unclear archives,
model packages, or helper code are redistributed under this artifact license.

Redistribution permission for third-party datasets, pretrained weights, cached
model artifacts, and local source-text stress data is not fully established in
this package. Before publishing a public artifact, confirm that redistribution
is permitted by the original dataset, model, project, and paper licenses. If
redistribution is not permitted, keep only preparation instructions and
checksums.

See `THIRD_PARTY_DATA.md` for the resource-by-resource inventory.

## Checksums

Run:

```bash
python scripts/build_manifest.py
```

The generated `artifact_manifest.json` includes SHA256 checksums for key
manuscript, script, result, and data-split files included in the artifact.

## Preprocessing

No additional preprocessing is required for the aggregate-table audit. Full
model reruns read the AST-token `func` sequences directly from the split files.

## Preparation if Bundled Data Cannot Be Redistributed

If the AST-token files or archives must be removed from a public release:

1. Obtain the upstream EaTVul-style AST-token resources under the applicable
   upstream terms.
2. Place the split files under `Code and Dataset/file/data/` with the filenames
   listed in the dataset table above.
3. Run `python scripts/eatvul_reproduce.py dataset-summary` and confirm the
   expected split counts.
4. Run `python scripts/build_manifest.py` to record local checksums.

True inserted spans, source diffs, CFGs, PDGs, and parser-validated source
contexts are not available in this artifact. The diagnostic deletion tables
therefore report token-removal proxy metrics rather than source-level repair or
insertion-span recovery.
