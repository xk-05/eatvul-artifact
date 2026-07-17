from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "paper_eatvul_defense_framework/latex_submission/main_jisa.tex",
    "paper_eatvul_defense_framework/latex_submission/main_jisa.pdf",
    "paper_eatvul_defense_framework/figures_submission_jisa/action_boundary.pdf",
    "results/jisa_evidence_bundle.json",
    "results/jisa_matched_budget_summary.csv",
    "results/jisa_confidence_sensitivity/confidence_adv_samples.csv",
    "manifests/jisa_final/FINAL_RUN_MANIFEST.json",
    "scripts/materialize_jisa_evidence.py",
]


def test_final_jisa_release_files_are_present() -> None:
    assert not [path for path in REQUIRED if not (ROOT / path).is_file()]


def test_private_archive_and_raw_splits_are_not_published() -> None:
    names = {path.name for path in ROOT.rglob("*") if ".git" not in path.parts}
    assert "Code and Dataset.zip" not in names
    assert not list(ROOT.glob("Code and Dataset/file/data/*_ast_*.json"))


def test_final_manuscript_is_the_three_rq_version() -> None:
    manuscript = ROOT / "paper_eatvul_defense_framework/latex_submission/main_jisa.tex"
    source = manuscript.read_text(encoding="utf-8")
    assert "Evidence Boundaries of AST-Token-Only Defenses" in source
    assert all(f"RQ{number}" in source for number in range(1, 4))
    assert "RQ4" not in source
