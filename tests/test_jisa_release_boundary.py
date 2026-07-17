import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

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


def test_public_final_evidence_has_no_machine_local_paths() -> None:
    public_metadata = [
        ROOT / "results" / "jisa_evidence_bundle.json",
        ROOT / "manifests" / "jisa_final" / "FINAL_RUN_MANIFEST.json",
        ROOT / "manifests" / "jisa_final" / "confidence_run_manifest.json",
    ]
    for path in public_metadata:
        text = path.read_text(encoding="utf-8")
        assert re.search(r"[A-Za-z]:\\", text) is None, path.relative_to(ROOT)


def test_sanitize_value_converts_known_execution_paths_to_relative_paths() -> None:
    from sanitize_jisa_paths import sanitize_value

    drive = "D:"
    assert sanitize_value(drive + r"\EatVul-Resources\Code and Dataset\file\data\a.json") == (
        "Code and Dataset/file/data/a.json"
    )
    assert sanitize_value(
        drive
        + r"\EatVul-Resources\.worktrees\nested-lodo-defense\results\jisa_revision"
    ) == "results/jisa_revision"
    assert sanitize_value(drive + r"\Anaconda\envs\eatvul\python.exe") == "python"
