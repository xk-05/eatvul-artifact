# Data Documentation

The main manuscript evaluates four EaTVul-style AST-token datasets:
ASTERISK, OPENSSL, CWE119, and CWE399. These split files are third-party or
derived third-party resources with redistribution terms that are not confirmed
in this release package. They are therefore not redistributed through public Git
tracking. Aggregate result CSVs needed for table audit remain in `results/`.

## Dataset Summary

When prepared locally, the AST-token split files should use these paths:

| Dataset | Role | Clean train | Clean test | ADV test | Local paths |
| --- | --- | ---: | ---: | ---: | --- |
| ASTERISK | Project-coherent | 880 | 367 | 50 | `Code and Dataset/file/data/asterisk_ast_*.json` |
| OPENSSL | Project-coherent | 520 | 213 | 50 | `Code and Dataset/file/data/openssl_ast_*.json` |
| CWE119 | Mixed-source stress setting | 5670 | 2451 | 200 | `Code and Dataset/file/data/cwe119_ast_*.json` |
| CWE399 | Mixed-source stress setting | 545 | 255 | 200 | `Code and Dataset/file/data/cwe399_ast_*.json` |

## Required and Optional Data

The lightweight aggregate-table audit uses the stored result CSV files under
`results/`, manuscript sources, and validation scripts. It does not require
redistributing the external AST-token split files.

Dataset-size checks, feature-importance recomputation, and full reruns of the
main TF-IDF/logistic-regression target, gate, anomaly-baseline, quarantine,
F1-constrained, and diagnostic-deletion experiments require the AST-token split
files to be prepared locally under `Code and Dataset/file/data/`.

Neural sanity-check reruns may additionally require pretrained CodeBERT or
other Hugging Face model files and local fine-tuned checkpoints. Those files are
not required for auditing the stored aggregate CSV values.

## Redistribution Status

The AST-token files came from a local EaTVul-style resource package. Their
upstream redistribution terms are not established in this package and they are
not covered by the repository MIT license. The public release records their
expected paths, sizes, and SHA256 checksums in `THIRD_PARTY_DATA.md`, but removes
the files from Git tracking.

Historical local archives (`Code and Dataset.zip`, `model.zip`), Apple metadata
files, EaTVul helper code under `Code and Dataset/file/code/`, model caches,
checkpoints, and pretrained weights are not part of the tracked public release.
Local copies may remain in an author or reviewer workspace, but they are
ignored to avoid implying redistribution under this artifact license.

See `THIRD_PARTY_DATA.md` for the resource-by-resource inventory.

## Checksums

Run:

```bash
python scripts/build_manifest.py
```

The generated `artifact_manifest.json` includes SHA256 checksums for tracked
artifact files such as manuscript sources, scripts, documentation, result CSVs,
and configuration sidecars. It intentionally excludes the license-unclear
external AST-token split files. Their pre-removal checksums are recorded in
`THIRD_PARTY_DATA.md`.

## Preparation for Full Reruns

To run commands that need the external AST-token data:

1. Obtain the upstream EaTVul-style AST-token resources under the applicable
   upstream terms.
2. Place the split files under `Code and Dataset/file/data/` with the filenames
   listed in the dataset table above.
3. Run `python scripts/eatvul_reproduce.py dataset-summary` and confirm the
   expected split counts.
4. Compare local file checksums against the inventory in `THIRD_PARTY_DATA.md`
   when using the same resource package.

True inserted spans, source diffs, CFGs, PDGs, and parser-validated source
contexts are not available in this artifact. The diagnostic deletion tables
therefore report token-removal proxy metrics rather than source-level repair or
insertion-span recovery.
