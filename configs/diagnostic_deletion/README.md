# Diagnostic Deletion Configuration

Fixed-window diagnostic deletion:

```bash
conda run -n eatvul python scripts/eatvul_localize_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-window-fpr 0.01 --window 1536 --stride 768 --max-spans 2 --candidate-windows 32 --min-prob-gain 0.005 --gate-on-benign
```

AST-token component diagnostic deletion:

```bash
conda run -n eatvul python scripts/eatvul_component_sanitize.py --datasets asterisk openssl cwe119 cwe399 --calibrate-component-fpr 0.01 --max-cluster 3 --max-spans 1 --candidate-components 16 --min-prob-gain 0.001 --gate-on-benign --calibration-items 200
```

These are diagnostic boundary tests, not deployable sanitizers.
