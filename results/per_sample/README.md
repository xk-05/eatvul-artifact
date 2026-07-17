# Per-sample Evidence

The final public sample-level evidence is
`results/jisa_confidence_sensitivity/confidence_adv_samples.csv`. It contains
2,500 adversarial sample-budget rows across four targets and five nominal
budgets. `python scripts/jisa_confidence_sensitivity.py verify` recomputes the
summary counts and rates from those rows and checks their recorded hashes.

Complete paired prediction logs are not available for every historical defense
layer. Do not manufacture missing rows. The final paper limits its claims to the
released evidence and records unavailable objects in `MISSING_OBJECTS.md`.
