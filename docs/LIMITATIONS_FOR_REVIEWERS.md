# Limitations for Reviewers

This artifact is intentionally bounded.

## Supported Claims

- AST-token sample-level evidence supports suspicious benign prediction
  detection under project-coherent calibration.
- Quarantine/review routing can reduce automatically accepted benign bypasses.
- Diagnostic token deletion tests did not demonstrate reliable automatic
  source-level sanitization.

## Unsupported Claims

- The artifact does not prove reliable automatic sanitization.
- The artifact does not provide broad adaptive robustness.
- The artifact does not fully reproduce every original EaTVul victim-model
  baseline or attack-generation stage.
- The artifact does not include complete paired prediction logs for all defense
  layers.
- Redistribution permissions for bundled third-party data archives, model
  archives, pretrained weights, and cached checkpoints are not fully established
  in this package; see `THIRD_PARTY_DATA.md`.
- Table 6 now has an executable feature-family export script, but the original
  manuscript row predates a saved per-split provenance file. The script writes
  a recomputed CSV and warns if it differs from the reported row.

## Missing Evidence

See `MISSING_OBJECTS.md` for the complete list. The most important missing
objects are source spans, source diffs, CFGs, PDGs, and source-to-token
mappings. Without those objects, token removal cannot be interpreted as verified
source repair.
