# Final Table and Figure Reproduction Map

The canonical manuscript is `paper_eatvul_defense_framework/latex_submission/main_jisa.tex`.
Run `python scripts/materialize_jisa_evidence.py` to regenerate the derived TeX
tables and vector figures from the public evidence.

| Manuscript item | Canonical output | Backing public evidence | Verification |
| --- | --- | --- | --- |
| Table 2: dataset roles and median token lengths | `latex_submission/generated/jisa_dataset_profile.tex` | `results/jisa_confidence_sensitivity/token_length_profile.csv` | exact fragment hash plus CSV parse |
| Table 3: matched screening at nominal 5% | `latex_submission/generated/jisa_matched_budget_5.tex` | `results/jisa_evidence_bundle.json`; `results/jisa_matched_budget_summary.csv` | verified 100-row matched-budget grid |
| Table 4: target-confidence baseline | `latex_submission/generated/jisa_confidence_baseline.tex` | `results/jisa_confidence_sensitivity/confidence_summary.csv`; `confidence_adv_samples.csv` | sample-row recomputation and exact fragment hash |
| Table 5: duplicate sensitivity | `latex_submission/generated/jisa_duplicate_sensitivity.tex` | `results/jisa_confidence_sensitivity/duplicate_sensitivity.csv` | confidence verifier and exact fragment hash |
| Table 6: cross-target screening stability | `latex_submission/generated/jisa_screening_stability.tex` | `results/jisa_matched_budget_summary.csv` | verified grid and exact fragment hash |
| Table 7: bounded CodeBERT feasibility | `latex_submission/generated/jisa_codebert_results.tex` | `results/jisa_evidence_bundle.json` | verified bundle and exact fragment hash |
| Table 8: token length versus 256-token limit | `latex_submission/generated/jisa_token_length.tex` | `results/jisa_confidence_sensitivity/token_length_profile.csv` | profile parse and exact fragment hash |
| Table 9: fixed deletion sensitivity | `latex_submission/generated/jisa_deletion_sensitivity.tex` | `results/jisa_evidence_bundle.json` | verified bundle and exact fragment hash |
| Figure 1: evidence-to-action boundary | `figures_submission_jisa/action_boundary.pdf` | conceptual boundary encoded in `scripts/materialize_jisa_evidence.py` | render inspection |
| Figure 2: capture versus review | `figures_submission_jisa/capture_vs_review.pdf` | `results/jisa_matched_budget_summary.csv` | regenerated curves and render inspection |
| Figure 3: residual bypass versus review | `figures_submission_jisa/residual_vs_review.pdf` | `results/jisa_matched_budget_summary.csv` | regenerated curves and render inspection |

Paths beginning with `latex_submission/` are relative to
`paper_eatvul_defense_framework/`. `scripts/check_reported_values.py` verifies
the final Tables 2--9 fragments and the complete backing grids. PDF figure bytes
can vary with Matplotlib/PDF metadata; rendered content is the appropriate
cross-environment comparison.

Older tables and PNG figures retained elsewhere in the repository belong to
earlier manuscript iterations and are not canonical for the final JISA paper.
