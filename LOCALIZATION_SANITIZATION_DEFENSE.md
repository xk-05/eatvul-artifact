# EaTVul Fine-Grained Localization and Sanitization Defense

This implementation upgrades the previous sample-level adversarial insertion detector into a locate-then-sanitize defense.
Because the released dataset stores AST-token sequences rather than recoverable source files or PDGs, the current defense operates on AST-token spans. The code is structured so a future source/PDG locator can replace the window scorer while keeping the same sanitization and evaluation pipeline.

## Entry Point

```powershell
conda run -n eatvul python scripts\eatvul_localize_sanitize.py `
  --datasets asterisk openssl cwe119 cwe399 `
  --calibrate-window-fpr 0.01 `
  --window 1536 `
  --stride 768 `
  --max-spans 2 `
  --candidate-windows 32 `
  --min-prob-gain 0.005 `
  --gate-on-benign
```

Optional cascade with the earlier sample-level insertion detector:

```powershell
conda run -n eatvul python scripts\eatvul_localize_sanitize.py `
  --datasets asterisk openssl cwe119 cwe399 `
  --calibrate-window-fpr 0.01 `
  --window 1536 `
  --stride 768 `
  --max-spans 2 `
  --candidate-windows 32 `
  --min-prob-gain 0.005 `
  --gate-on-benign `
  --sample-gate `
  --sample-gate-fpr 0.50
```

## Method

1. Train the target vulnerability detector on clean AST-token training data.
2. Build background token statistics from the same clean training split.
3. Slide a fixed-size window over each function-level AST-token sequence.
4. Score each window with source-token and AST-structure anomaly features:
   rare/unseen token ratio, token IDF, local bigram NLL, isolated identifier ratio, declaration density, AST structural-token density, function-definition density, control/type ratios, and depth proxy.
5. Calibrate a deletion threshold from clean training windows.
6. Use model-guided localization: a suspicious window is deleted only if deleting it raises the target model's vulnerable probability by at least `--min-prob-gain`.
7. Re-run the vulnerability detector on the sanitized token sequence.

The default deployed flow is gated: only samples initially predicted as benign enter localization, because EaTVul's attack objective is to hide vulnerable samples as benign.

## Results

Previous sample-level front detector, calibrated to about 10% clean non-vulnerable false positives:

| dataset | clean F1 before | clean F1 after | baseline ASR | defended ASR | ASR reduction |
| --- | --- | --- | --- | --- | --- |
| asterisk | 0.769 | 0.455 | 0.640 | 0.360 | 0.280 |
| openssl | 0.829 | 0.693 | 0.760 | 0.120 | 0.640 |
| cwe119 | 0.943 | 0.883 | 0.720 | 0.660 | 0.060 |
| cwe399 | 0.784 | 0.718 | 0.695 | 0.625 | 0.070 |

Fine-grained local sanitize, no sample gate:

| dataset | clean F1 before | clean F1 after | baseline ASR | sanitized ASR | ASR reduction | ADV modified | ADV removed ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| asterisk | 0.769 | 0.274 | 0.640 | 0.600 | 0.040 | 0.040 | 0.040 |
| openssl | 0.829 | 0.819 | 0.760 | 0.700 | 0.060 | 0.760 | 0.434 |
| cwe119 | 0.944 | 0.943 | 0.720 | 0.720 | 0.000 | 0.230 | 0.207 |
| cwe399 | 0.788 | 0.788 | 0.695 | 0.695 | 0.000 | 0.375 | 0.318 |

Fine-grained local sanitize with sample-level gate (`--sample-gate-fpr 0.50`):

| dataset | clean F1 before | clean F1 after | baseline ASR | sanitized ASR | ASR reduction | ADV modified | ADV removed ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| asterisk | 0.769 | 0.388 | 0.640 | 0.600 | 0.040 | 0.040 | 0.040 |
| openssl | 0.829 | 0.829 | 0.760 | 0.720 | 0.040 | 0.580 | 0.304 |
| cwe119 | 0.944 | 0.944 | 0.720 | 0.720 | 0.000 | 0.190 | 0.183 |
| cwe399 | 0.788 | 0.788 | 0.695 | 0.695 | 0.000 | 0.160 | 0.160 |

Saved outputs:

- `results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv`
- `results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_sample_gate0.5_results.csv`
- Sanitized JSONL files are saved in `results/eatvul_local_defense/`.

## Interpretation

The new defense now performs actual token-span localization and deletion instead of only front-running the vulnerability model with a binary adversarial detector.
On OpenSSL, deleting localized spans recovers part of the attack success while preserving clean F1. On Asterisk, the localizer exposes a key limitation of AST-token-only defense: deleting suspicious declaration-heavy windows can create false positives unless the sample-level gate is conservative.

The earlier sample-level detector is still stronger as a blocking defense because it does not need to identify exact insertion boundaries. The new local sanitizer is the correct scaffold for a paper-level defense, but it needs source-level or PDG-level boundaries to become reliable across all datasets.

## Next Research Step

To make this genuinely PDG-level:

1. Recover or regenerate source functions for each AST-token sample.
2. Build AST and PDG nodes with Joern or Tree-sitter plus a lightweight data-dependence extractor.
3. Replace fixed token windows with candidate inserted subtrees or PDG-isolated components.
4. Score each component by identifier novelty, cross-project token rarity, control reachability, data-dependence isolation, and target-model probability gain.
5. Delete or downweight only whole syntactic/PDG components, not arbitrary token windows.
