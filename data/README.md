# Data Directory Notes

The public Git repository does not redistribute the EaTVul-style AST-token split
files because their redistribution terms are not confirmed in this package.
Aggregate manuscript tables can be audited from the tracked result CSVs under
`results/`.

For dataset-size checks, feature-importance recomputation, and full experiment
reruns, prepare the external AST-token resources locally at:

```text
Code and Dataset/file/data/
```

Expected filenames:

- `asterisk_ast_train.json`, `asterisk_ast_test.json`, `asterisk_ast_test_ADV.json`
- `openssl_ast_train.json`, `openssl_ast_test.json`, `openssl_ast_test_ADV.json`
- `cwe119_ast_train.json`, `cwe119_ast_test.json`, `cwe119_ast_test_ADV.json`
- `cwe399_ast_train.json`, `cwe399_ast_test.json`, `cwe399_ast_test_ADV.json`

After preparing the files, run:

```bash
python scripts/eatvul_reproduce.py dataset-summary
```

The expected split counts and pre-removal checksums are documented in
`DATA.md` and `THIRD_PARTY_DATA.md`.

This `data/` directory may contain small supplementary metadata files such as:

- `data/extension_projects/linevul_bigvul_summary.json`

Do not add private credentials, API keys, raw restricted datasets, model
weights, checkpoints, archives, or cache directories here.
