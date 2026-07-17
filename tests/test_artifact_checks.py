from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def test_artifact_structure_check_passes() -> None:
    result = run_script("scripts/check_artifact.py")
    assert "Artifact check passed" in result.stdout


def test_reported_values_check_passes() -> None:
    result = run_script("scripts/check_reported_values.py")
    assert "Reported-value check passed" in result.stdout
    assert "Tables 2-9" in result.stdout


def test_text_integrity_discovers_final_manifests_and_manuscript() -> None:
    import check_text_integrity as integrity

    files = [
        Path("manifests/jisa_final/FINAL_RUN_MANIFEST.json"),
        Path("results/jisa_evidence_bundle.json"),
    ]
    assert integrity.json_files(files) == files
    assert integrity.CANONICAL_MANUSCRIPT.name == "main_jisa.tex"


def test_manifest_includes_final_jisa_release() -> None:
    run_script("scripts/build_manifest.py")
    manifest = json.loads((ROOT / "artifact_manifest.json").read_text(encoding="utf-8"))
    paths = {item["path"] for item in manifest["files"]}
    assert {
        "paper_eatvul_defense_framework/latex_submission/main_jisa.pdf",
        "paper_eatvul_defense_framework/figures_submission_jisa/action_boundary.pdf",
        "results/jisa_evidence_bundle.json",
        "manifests/jisa_final/FINAL_RUN_MANIFEST.json",
        "requirements_jisa.txt",
    } <= paths


def test_feature_importance_keeps_packaged_csv_without_external_splits(tmp_path, monkeypatch, capsys) -> None:
    import export_gate_feature_importance as feature_importance

    out_dir = tmp_path / "results"
    out_dir.mkdir()
    (out_dir / "gate_feature_family_importance.csv").write_text(
        "\n".join(
            [
                "split,rare_token,unseen_token,bigram_nll,ast_structure",
                "LODO_average,11.465514530883537,52.873029770370906,14.540366125432438,21.121089573313114",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    missing_dir = tmp_path / "missing-data"
    monkeypatch.setattr(feature_importance, "OUT_DIR", out_dir)
    monkeypatch.setattr(
        feature_importance,
        "DATASETS",
        {
            "openssl": {
                "test": missing_dir / "openssl_ast_test.json",
                "adv": missing_dir / "openssl_ast_test_ADV.json",
            }
        },
    )

    assert feature_importance.main() == 0
    assert "External AST-token split files are not available" in capsys.readouterr().out
