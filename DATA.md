# Data Documentation

## Evaluated roles

The final manuscript evaluates four EaTVul-style serialized AST-token targets:

| Target | Train | Unattacked test | ADV test |
| --- | ---: | ---: | ---: |
| ASTERISK | 880 | 367 | 50 |
| OPENSSL | 520 | 213 | 50 |
| CWE119 | 5670 | 2451 | 200 |
| CWE399 | 545 | 255 | 200 |

Counts and token-length summaries used by the final paper are released in
`results/jisa_confidence_sensitivity/token_length_profile.csv` and materialized
as Table 2.

## Public derived evidence

- `results/jisa_evidence_bundle.json`: verified evidence for the matched-budget,
  model-coverage, and deletion analyses.
- `results/jisa_matched_budget_summary.csv`: 100 target/method/budget rows.
- `results/jisa_confidence_sensitivity/confidence_summary.csv`: 20 target/budget
  summary rows.
- `results/jisa_confidence_sensitivity/confidence_adv_samples.csv`: 2,500
  sample-budget evaluation rows used by the confidence verifier.
- `results/jisa_confidence_sensitivity/duplicate_sensitivity.csv`: 15 pooled
  duplicate-control rows.
- `results/jisa_confidence_sensitivity/token_length_profile.csv`: 12 role-level
  token-length rows.

The matching hashes and environment metadata are recorded in
`manifests/jisa_final/` and
`results/jisa_confidence_sensitivity/run_manifest.json`.

## Non-public inputs

The repository does not redistribute `Code and Dataset.zip` or raw AST-token
splits. Their redistribution terms are not established for this release. A
locally authorized full-retraining layout is:

```text
Code and Dataset/file/data/
  asterisk_ast_train.json
  asterisk_ast_test.json
  asterisk_ast_test_ADV.json
  openssl_ast_train.json
  openssl_ast_test.json
  openssl_ast_test_ADV.json
  cwe119_ast_train.json
  cwe119_ast_test.json
  cwe119_ast_test_ADV.json
  cwe399_ast_train.json
  cwe399_ast_test.json
  cwe399_ast_test_ADV.json
```

The fast audit, table materialization, and confidence-output verification do not
require these files. Full model retraining does.

True inserted spans, source diffs, source-to-token mappings, CFGs, PDGs, and
compiler/security validation contexts are unavailable. This absence is part of
the paper's evidence boundary and prevents a source-repair claim.
