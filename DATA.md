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

## Redistribution Status

The AST-token files are part of the local EaTVul resource package. The
repository also contains historical release archives. Before publishing a public
artifact, confirm that redistribution is permitted by the original dataset and
paper licenses. If redistribution is not permitted, keep only preparation
instructions and checksums.

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
