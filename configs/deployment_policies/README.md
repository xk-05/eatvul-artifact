# Deployment Policy Configuration

Quarantine policy:

```bash
conda run -n eatvul python scripts/eatvul_quarantine_defense.py --clean-block-budget 0.1
```

F1-constrained hard override:

```bash
conda run -n eatvul python scripts/eatvul_f1_constrained_defense.py --max-clean-f1-drop 0.03
```

Quarantine is review routing. It should not be described as prediction
correction or automatic source repair.
