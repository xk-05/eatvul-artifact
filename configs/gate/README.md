# Gate Configuration

Main sample-level gate row:

```bash
conda run -n eatvul python scripts/eatvul_defense.py --leave-one-dataset-out --calibrate-clean-fpr 0.1
```

Key settings:

- leave-one-dataset-out training;
- gate-positive examples are source-dataset EaTVul-style adversarial insertion
  samples;
- gate-negative examples are source-dataset clean vulnerable samples, i.e.,
  vulnerable functions before adversarial insertion;
- target-dataset clean non-vulnerable calibration;
- clean FPR budget approximately 0.10;
- random forest insertion gate with handcrafted AST-token features.

Source result:

```text
results/eatvul_defense/lodo_calib_fpr_0.1_results.csv
```
