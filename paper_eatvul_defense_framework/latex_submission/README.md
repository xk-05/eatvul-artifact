# EaTVul Defense LaTeX Submission Draft

This folder contains the canonical LaTeX manuscript for the EaTVul AST-token defense boundary study and the existing experiment outputs. The source filename is inherited from earlier USENIX-style drafts; `main.tex` is retained as a neutral compatibility entry point for the JISA/Elsevier submission package.

## Files

- `main_usenix_style_round3_clean.tex`: canonical manuscript source.
- `main.tex`: compatibility entrypoint that inputs the canonical source, so older build commands do not compile the obsolete framework-centered draft.
- `references.bib`: BibTeX references used by the manuscript.
- `build_citation_bib_check/main_usenix_style_round3_clean.pdf`: current compiled PDF for the AST-token capability-boundary version.

## Compile

From the repository root:

```powershell
$env:PYTHONUTF8='1'
python 'C:/Users/Administrator/.codex/plugins/cache/openai-bundled/latex/0.2.3/scripts/compile_latex.py' `
  'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex' `
  --compiler tectonic `
  --output-directory 'D:/EatVul-Resources/paper_eatvul_defense_framework/latex_submission/build_citation_bib_check' `
  --json
```

The manuscript imports figures from:

- `../figures_submission/*.png`

Key result sources:

- `results/eatvul_defense/lodo_calib_fpr_0.1_results.csv`
- `results/eatvul_defense/gate_feature_family_importance.csv`
- `results/eatvul_anomaly_baselines/anomaly_baseline_results.csv`
- `results/neural_target_gate/neural_target_gate_results.csv`
- `results/eatvul_local_defense/localize_sanitize_w1536_s768_fpr0.01_max2_guided_benign_gate_no_sample_gate_results.csv`
- `results/eatvul_component_defense/component_sanitize_fpr0.01_cluster3_max1_benign_gate_no_sample_gate_results.csv`
- `results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv`
- `results/eatvul_f1_constrained_defense/f1_constrained_maxf1drop0.03_benignonly_results.csv`

The RQ1 sample-level gate table uses the 10% clean-FPR calibrated LODO output. Gate-positive examples are source-dataset adversarial insertion samples; gate-negative examples are source-dataset clean vulnerable samples. The 10% deployment threshold is calibrated on target clean non-vulnerable samples. The AST-token component deletion rows use the cluster-3, max-span-1 boundary-test output with `min_prob_gain = 0.001`; the fixed-window deletion rows use `min_prob_gain = 0.005`.

The manuscript's central claim is not that complete automatic sanitization is solved. It argues that AST-token evidence supports detection and quarantine, while reliable automatic sanitization remains blocked by missing source spans, insertion boundaries, CFGs, and PDGs.
