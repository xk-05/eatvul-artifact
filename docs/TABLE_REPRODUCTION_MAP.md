# Table and Figure Reproduction Map

| Manuscript item | Source script | Source data/result file | Output file | Reproducibility from current files | Notes |
| --- | --- | --- | --- | --- | --- |
| Table 2: dataset sizes | `scripts/eatvul_reproduce.py dataset-summary` | Local external `Code and Dataset/file/data/*_ast_*.json` | console CSV summary | Reproducible after external data preparation | Counts verified for ASTERISK, OPENSSL, CWE119, CWE399. |
| Table 4: sample-level gate under hard override | `scripts/eatvul_defense.py` | `results/eatvul_defense/lodo_calib_fpr_0.1_results.csv` | same CSV | Fully reproducible for aggregate rows | Full rerun requires `conda run -n eatvul`. |
| Table 5: aggregate-count uncertainty checks | aggregate recomputation from Table 4 counts | `results/eatvul_defense/lodo_calib_fpr_0.1_results.csv` | manuscript table | Reproducible from aggregate counts | Fisher tests are aggregate-count checks, not paired per-sample tests. |
| Table 6: gate feature-family contribution | `scripts/export_gate_feature_importance.py` | Local external `Code and Dataset/file/data/*_ast_*.json`; `results/eatvul_defense/gate_feature_family_importance.csv` | `results/eatvul_defense/gate_feature_family_importance.csv` | Stored CSV auditable; recomputation requires external data preparation | The manuscript reports the recomputed `LODO_average` rounded to one decimal. |
| Table 7: anomaly baseline comparison | `scripts/eatvul_anomaly_baselines.py` | `results/eatvul_anomaly_baselines/anomaly_baseline_results.csv` | same CSV | Fully reproducible for aggregate rows | OPENSSL and ASTERISK rows are reported. |
| Table 8: CodeBERT bounded sanity check | `scripts/eatvul_neural_target_gate.py` | `results/neural_target_gate/neural_target_gate_results.csv` | same CSV | Aggregate-file reproducible; full rerun is expensive | Requires local model/dependency setup. |
| Table 9: diagnostic deletion boundary-test summary | `scripts/eatvul_localize_sanitize.py`; `scripts/eatvul_component_sanitize.py` | fixed-window and component CSVs | same CSVs | Fully reproducible for aggregate rows | Deletion tests are diagnostic, not deployable sanitizers. |
| Table 10: quarantine policy | `scripts/eatvul_quarantine_defense.py` | `results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv` | same CSV | Fully reproducible for aggregate rows | Residual silent-bypass rate counts automatically accepted benign bypasses. |
| Table 11: F1-constrained hard override | `scripts/eatvul_f1_constrained_defense.py` | `results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv` | same CSV | Fully reproducible for aggregate rows | Hard override is a diagnostic policy. |
| Table 12: integrated comparison | manuscript synthesis | Tables 4, 7, 9, 10, 11 | manuscript table | Auditable from cited tables | Contains qualitative comparator rows. |
| Table 13: supplementary diagnostic material excluded from main claims | manuscript synthesis | Supplementary source-text stress-check files under `results/extension_experiments/` where present | manuscript appendix table | Auditable from cited files and manuscript text | These diagnostics are excluded from the main evidence and should not be used as primary claims. |
| Table 14: BiLSTM-attention supplementary neural reference | `scripts/eatvul_neural_target_gate.py` | `results/neural_target_gate/neural_target_gate_results.csv` | same CSV | Aggregate-file reproducible; full rerun is expensive | Supplementary bounded neural reference only. |
| Table 15: diagnostic deletion token-removal proxy metrics | `scripts/eatvul_localize_sanitize.py`; `scripts/eatvul_component_sanitize.py` | fixed-window and component CSVs | same CSVs | Fully reproducible for aggregate rows | Removed-token ratios are proxies, not insertion-span recall. |
| Table 16: full integrated comparison | manuscript synthesis | Tables 4, 7, 9, 10, 11, and qualitative comparison rows | manuscript appendix table | Auditable from cited tables | Full comparison table combining supported, diagnostic, and qualitative rows. |
| Figure 1 | manuscript figure asset | `paper_eatvul_defense_framework/figures_submission/` | `dataset_overview_en.png` or conceptual figure asset | Auditable from figure file | Visual asset checked by `scripts/make_figures.py`. |
| Figure 2 | figure-generation scripts and stored figure | `paper_eatvul_defense_framework/figures_submission/sample_gate_results_en.png` | same PNG | Auditable from stored figure | Regeneration depends on local plotting scripts. |
| Figure 3 | figure-generation scripts and stored figure | `paper_eatvul_defense_framework/figures_submission/window_sanitize_results_en.png` | same PNG | Auditable from stored figure | Regeneration depends on local plotting scripts. |

## Items Not Fully Reproducible from Current Files

- Complete paired prediction logs for all defense layers are not present.
- True inserted spans, source diffs, CFGs, PDGs, and compiler-validated adaptive
  snippets are not present.
- Some figure/table synthesis rows are auditable from result files and
  manuscript text but do not yet have a single standalone regeneration script.
