# Diagnostic Deletion Configuration

Fixed-window diagnostic deletion:

```bash
conda run -n eatvul python scripts/eatvul_localize_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-window-fpr 0.01 --window 1536 --stride 768 --max-spans 2 --candidate-windows 32 --min-prob-gain 0.005 --gate-on-benign
```

AST-token component diagnostic deletion:

```bash
conda run -n eatvul python scripts/eatvul_component_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-component-fpr 0.01 --max-cluster 3 --max-spans 1 --candidate-components 16 --min-prob-gain 0.001 --gate-on-benign --calibration-items 200
```

The reported fixed-window rows use `min_prob_gain = 0.005`. The reported
AST-token component rows use `min_prob_gain = 0.001`, even though the component
script default may be different. Audit the sidecar config JSON files beside the
reported CSVs when reproducing Table 9 and Table 15.

These are diagnostic boundary tests, not deployable sanitizers.
