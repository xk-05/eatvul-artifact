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

## Missing Evidence

See `MISSING_OBJECTS.md` for the complete list. The most important missing
objects are source spans, source diffs, CFGs, PDGs, and source-to-token
mappings. Without those objects, token removal cannot be interpreted as verified
source repair.
