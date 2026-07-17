#!/usr/bin/env python
"""Build a SHA256 manifest for key artifact files."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifact_manifest.json"

INCLUDE_PATTERNS = [
    "README.md",
    "ARTIFACT.md",
    "REPRODUCIBILITY.md",
    "DATA.md",
    "THIRD_PARTY_DATA.md",
    "MISSING_OBJECTS.md",
    "CITATION.cff",
    "LICENSE",
    "requirements.txt",
    "requirements_jisa.txt",
    "environment.yml",
    "pyproject.toml",
    "Makefile",
    "highlights.md",
    "JISA_REVISION_NOTES.md",
    "SUBMISSION_JISA.md",
    ".gitattributes",
    ".gitignore",
    ".github/workflows/*.yml",
    "configs/**/*.md",
    "docs/*.md",
    "manifests/**/*.json",
    "paper_eatvul_defense_framework/latex_submission/*.tex",
    "paper_eatvul_defense_framework/latex_submission/*.pdf",
    "paper_eatvul_defense_framework/latex_submission/*.bib",
    "paper_eatvul_defense_framework/latex_submission/*.txt",
    "paper_eatvul_defense_framework/latex_submission/*.cls",
    "paper_eatvul_defense_framework/latex_submission/*.sty",
    "paper_eatvul_defense_framework/latex_submission/*.bst",
    "paper_eatvul_defense_framework/latex_submission/generated/*.tex",
    "paper_eatvul_defense_framework/latex_submission/thumbnails/*.jpeg",
    "paper_eatvul_defense_framework/figures_submission/*.png",
    "paper_eatvul_defense_framework/figures_submission_jisa/*.pdf",
    "scripts/*.py",
    "tests/*.py",
    "results/**/*.csv",
    "results/**/*.json",
    "results/**/*_config.json",
    "results/**/*.txt",
]

EXCLUDE_PARTS = {
    "__pycache__",
    "checkpoint-best-acc",
}

MAX_SIZE = 50 * 1024 * 1024


def git_tracked_paths() -> set[str] | None:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return set(output.splitlines())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def include_file(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return False
    return path.is_file() and path.stat().st_size <= MAX_SIZE


def main() -> int:
    files: dict[str, Path] = {}
    tracked_paths = git_tracked_paths()
    for pattern in INCLUDE_PATTERNS:
        for path in ROOT.glob(pattern):
            rel = path.relative_to(ROOT).as_posix()
            if tracked_paths is not None and rel not in tracked_paths:
                continue
            if include_file(path):
                files[rel] = path
    manifest = {
        "schema": "jisa-eatvul-artifact-manifest-v1",
        "file_count": len(files),
        "files": [
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for rel, path in sorted(files.items())
        ],
    }
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
