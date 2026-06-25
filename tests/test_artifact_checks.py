from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
