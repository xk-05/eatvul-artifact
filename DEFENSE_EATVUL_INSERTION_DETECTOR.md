  # EaTVul Insertion-Defense Prototype

## Goal

EaTVul shows that inserting harmless-looking dead-code snippets can make vulnerable samples bypass vulnerability detectors.
This prototype adds a front-end detector for EaTVul-style inserted snippets and fuses that result with the vulnerability
detector output.

Because the released data only provides AST-token sequences and final adversarial samples, not exact inserted snippet
boundaries, this implementation is sample-level:

1. classify an input AST sequence as clean or adversarially inserted;
2. if it is detected as adversarial, raise the final output to vulnerable;
3. otherwise keep the vulnerability detector result.

When source-level snippet boundaries are available, this same detector can be extended from sample-level classification
to window-level localization and deletion.

## Implemented Signals

The detector combines two views.

Token/source proxy view:

- TF-IDF token and token-bigram features
- rare token ratio
- unseen token ratio
- mean and 95th percentile token IDF
- local bigram negative log likelihood as a perplexity proxy
- identifier/name-like token ratio
- repeated variable/name ratio
- underscore and digit naming ratios

AST/structure proxy view:

- AST structural token ratio
- `LEAF_NODE`, `FUNCTION_DEF`, `SELECTION`, `ITERATION` ratios
- control-statement token ratio
- type-token ratio
- IO-token ratio
- numeric-depth max/mean
- longest structural/control-token run ratio

The current public release has AST tokens but no PDG, so data-dependency isolation and control-flow reachability are
implemented as AST-token proxies rather than true PDG features.

## Reproduction Command

```powershell
python scripts\eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.10
```

Evaluation setup:

- target vulnerability detector: lightweight TF-IDF + logistic regression trained on each dataset train split
- insertion detector: random forest trained on the other three datasets' clean/ADV splits
- threshold: calibrated on the target clean non-vulnerable test samples to keep clean false positives near 10%
- defense: if insertion detector fires, final label is vulnerable

This is a reproducible benchmark for the defense idea. It is not a direct reproduction of the paper's CodeBERT/Asteria/LineVul
tables because the public repo does not include all victim checkpoints and full attack-pool generation artifacts.

## Result

| Dataset | Clean F1 Before Defense | Clean F1 After Defense | Baseline ASR | Detector Recall on ADV | Clean Non-Vul FPR | Defended ASR | ASR Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Asterisk | 0.769 | 0.455 | 0.640 | 0.280 | 0.104 | 0.360 | 0.280 |
| OpenSSL | 0.829 | 0.693 | 0.760 | 0.740 | 0.102 | 0.120 | 0.640 |
| CWE119 | 0.943 | 0.883 | 0.720 | 0.060 | 0.100 | 0.660 | 0.060 |
| CWE399 | 0.784 | 0.718 | 0.695 | 0.070 | 0.127 | 0.625 | 0.070 |

Saved CSV:

```text
results/eatvul_defense/lodo_calib_fpr_0.1_results.csv
```

## Interpretation

The front-end detector substantially reduces attack success on OpenSSL and moderately reduces it on Asterisk under a
10% clean false-positive budget. Cross-dataset generalization is weak on CWE119 and CWE399, which suggests that the
current released ADV samples differ by dataset family and that a production detector should be trained with more diverse
clean/adversarial snippets or calibrated per project.

The clean F1 drop shows the expected cost of a conservative front-end defense: some clean non-vulnerable samples are
promoted to vulnerable when the detector suspects insertion. The threshold can be tuned with `--calibrate-clean-fpr`.

## Next Improvements

- train a window-level detector if source-code or exact insertion spans are available
- add true PDG features: dead-code reachability, data-dependency isolation, def-use orphan ratio
- use vulnerability-model hidden states instead of TF-IDF features
- replace hard override with probability fusion:
  `final_vuln_score = max(vuln_score, insertion_score * alpha)`
- evaluate against full CodeBERT checkpoints once CPU/GPU budget allows full target training
