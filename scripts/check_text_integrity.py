#!/usr/bin/env python
"""Check text-file integrity for the public artifact release."""

from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {
    ".py",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".tex",
    ".bib",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".cff",
}
TEXT_NAMES = {
    ".gitattributes",
    ".gitignore",
    "Makefile",
    "requirements.txt",
    "environment.yml",
    "pyproject.toml",
    "CITATION.cff",
}
CORE_DOCS = [
    "README.md",
    "ARTIFACT.md",
    "REPRODUCIBILITY.md",
    "DATA.md",
    "THIRD_PARTY_DATA.md",
    "SUBMISSION.md",
    "docs/RUNBOOK.md",
    "docs/TABLE_REPRODUCTION_MAP.md",
]
CORE_FILE_MIN_LINES = {
    "scripts/eatvul_defense.py": 50,
    "scripts/check_artifact.py": 50,
    "scripts/check_reported_values.py": 50,
    "scripts/check_text_integrity.py": 50,
    "scripts/export_gate_feature_importance.py": 50,
    "scripts/eatvul_reproduce.py": 50,
    "scripts/make_tables.py": 20,
    "scripts/make_figures.py": 20,
    "scripts/build_manifest.py": 50,
    "results/eatvul_defense/lodo_calib_fpr_0.1_results.csv": 5,
    "results/eatvul_defense/gate_feature_family_importance.csv": 5,
    "results/eatvul_anomaly_baselines/anomaly_baseline_results.csv": 5,
    "results/neural_target_gate/neural_target_gate_results.csv": 3,
    "results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv": 5,
    "requirements.txt": 5,
    "environment.yml": 5,
    "pyproject.toml": 5,
    "Makefile": 10,
    ".gitignore": 10,
    ".gitattributes": 10,
    "paper_eatvul_defense_framework/latex_submission/main.tex": 2,
    "paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex": 100,
    "paper_eatvul_defense_framework/latex_submission/references.bib": 20,
}
REQUIRED_GITATTRIBUTES_RULES = {
    "* text=auto eol=lf",
    "*.py text eol=lf",
    "*.csv text eol=lf",
    "*.json text eol=lf",
    "*.jsonl text eol=lf",
    "*.md text eol=lf",
    "*.tex text eol=lf",
    "*.bib text eol=lf",
    "*.yml text eol=lf",
    "*.yaml text eol=lf",
    "*.toml text eol=lf",
    "Makefile text eol=lf",
    "requirements.txt text eol=lf",
}
REQUIRED_GITIGNORE_RULES = {
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".venv/",
    "venv/",
    ".hf_cache/",
    ".cache/",
    "cache/",
    "model/",
    "models/",
    "checkpoint*/",
    "checkpoints/",
    "huggingface/",
    "results/**/checkpoint-best-acc/",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.pt",
    "*.bin",
    "*.pkl",
    "*.joblib",
    "Code and Dataset/",
    "Code and Dataset.zip",
    "model.zip",
}
REQUIRED_MAKE_TARGETS = {
    "check",
    "verify",
    "text-integrity",
    "text-check",
    "compile",
    "artifact",
    "reported-values",
    "feature-importance",
    "table-check",
    "dataset-summary",
}
KEY_CSV_MIN_ROWS = {
    "results/eatvul_defense/lodo_calib_fpr_0.1_results.csv": 4,
    "results/eatvul_defense/gate_feature_family_importance.csv": 5,
    "results/eatvul_anomaly_baselines/anomaly_baseline_results.csv": 4,
    "results/neural_target_gate/neural_target_gate_results.csv": 2,
    "results/eatvul_quarantine_defense/quarantine_cleanblock0.1_benignonly_results.csv": 4,
}
BAD_PYTHON_PATTERNS = [
    re.compile(r"\bimport[ \t]+\w+[^\n;]*[ \t]+import[ \t]+\w+"),
    re.compile(r"\bfrom[ \t]+\S+[ \t]+import[ \t]+\S+[^\n;]*[ \t]+from[ \t]+"),
    re.compile(r"\bdef[ \t]+\w+\([^)]*\)[^\n;]*[ \t]+import[ \t]+\w+"),
]


def git_files() -> list[Path]:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [
            path.relative_to(ROOT)
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]
    return [Path(line) for line in output.splitlines() if line]


def line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_line_endings(files: list[Path], errors: list[str]) -> None:
    checked = 0
    for rel in files:
        path = ROOT / rel
        if rel.suffix.lower() not in TEXT_SUFFIXES and rel.name not in TEXT_NAMES:
            continue
        if not path.exists():
            continue
        checked += 1
        data = path.read_bytes()
        crlf = data.count(b"\r\n")
        cr_only = data.count(b"\r") - crlf
        if crlf or cr_only:
            fail(errors, f"{rel}: contains CR bytes (CRLF={crlf}, CR-only={cr_only})")
    print(f"Text line endings: {checked} tracked text files checked")


def check_core_line_counts(errors: list[str]) -> None:
    checked = 0
    for rel, min_lines in CORE_FILE_MIN_LINES.items():
        path = ROOT / rel
        if not path.exists():
            fail(errors, f"{rel}: missing core artifact file")
            continue
        checked += 1
        data = path.read_bytes()
        lines = line_count(data)
        if lines < min_lines:
            fail(errors, f"{rel}: expected at least {min_lines} lines, found {lines}")
        if lines <= 2 and len(data) > 80:
            fail(errors, f"{rel}: suspiciously collapsed text file ({lines} lines)")
    print(f"Core file line counts: {checked} files checked")


def check_python(files: list[Path], errors: list[str]) -> None:
    python_files = [rel for rel in files if rel.suffix == ".py"]
    for rel in python_files:
        path = ROOT / rel
        text = read_text(path)
        lines = text.splitlines()
        if len(lines) <= 2:
            fail(errors, f"{rel}: suspiciously short Python file ({len(lines)} lines)")
        if lines and lines[0].startswith("#!"):
            shebang_payload = lines[0][2:].strip()
            if any(marker in shebang_payload for marker in (" import ", " def ", " class ")):
                fail(errors, f"{rel}: shebang line appears to contain Python code")
        for line_number, line in enumerate(lines, start=1):
            code_line = line.split("#", 1)[0]
            for pattern in BAD_PYTHON_PATTERNS:
                if pattern.search(code_line):
                    fail(errors, f"{rel}:{line_number}: suspicious collapsed-import pattern")
        try:
            ast.parse(text, filename=str(rel))
        except SyntaxError as exc:
            fail(errors, f"{rel}: Python syntax error: {exc}")
    print(f"Python syntax: {len(python_files)} tracked Python files checked")


def check_csv(files: list[Path], errors: list[str]) -> None:
    csv_files = [
        rel for rel in files if rel.as_posix().startswith("results/") and rel.suffix == ".csv"
    ]
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        pd = None

    for rel in csv_files:
        path = ROOT / rel
        if pd is not None:
            try:
                df = pd.read_csv(path)
            except Exception as exc:  # pragma: no cover - diagnostic path
                fail(errors, f"{rel}: pandas.read_csv failed: {exc}")
                continue
            rows, cols = df.shape
        else:
            try:
                with path.open(newline="", encoding="utf-8") as handle:
                    parsed = list(csv.reader(handle))
            except Exception as exc:
                fail(errors, f"{rel}: csv.reader failed: {exc}")
                continue
            rows = max(len(parsed) - 1, 0)
            cols = len(parsed[0]) if parsed else 0

        if rows <= 0:
            fail(errors, f"{rel}: no data rows")
        if cols <= 1:
            fail(errors, f"{rel}: too few columns ({cols})")
        min_rows = KEY_CSV_MIN_ROWS.get(rel.as_posix())
        if min_rows is not None and rows < min_rows:
            fail(errors, f"{rel}: expected at least {min_rows} rows, found {rows}")

        if rel.as_posix() == "results/eatvul_defense/gate_feature_family_importance.csv":
            if pd is not None:
                splits = set(df["split"].astype(str))
            else:
                splits = {row[0] for row in parsed[1:]}
            if "LODO_average" not in splits:
                fail(errors, f"{rel}: missing LODO_average row")

    print(f"CSV parse: {len(csv_files)} tracked result CSV files checked")


def check_json(files: list[Path], errors: list[str]) -> None:
    json_files = [
        rel
        for rel in files
        if rel.as_posix().startswith("results/") and rel.suffix in {".json", ".jsonl"}
    ]
    for rel in json_files:
        path = ROOT / rel
        try:
            if rel.suffix == ".jsonl":
                rows = [line for line in read_text(path).splitlines() if line.strip()]
                for line in rows:
                    json.loads(line)
                if not rows:
                    fail(errors, f"{rel}: empty JSONL file")
            else:
                json.loads(read_text(path))
        except Exception as exc:
            fail(errors, f"{rel}: JSON parse failed: {exc}")
    print(f"JSON parse: {len(json_files)} tracked result JSON/JSONL files checked")


def check_requirements(errors: list[str]) -> None:
    path = ROOT / "requirements.txt"
    lines = [
        line.strip()
        for line in read_text(path).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(lines) < 3:
        fail(errors, "requirements.txt: fewer than three non-comment dependency lines")
    joined = " ".join(lines)
    if "#" in joined and len(lines) == 1:
        fail(errors, "requirements.txt: dependencies appear to be swallowed by a comment")
    print(f"Requirements: {len(lines)} dependency lines checked")


def normalized_rule_lines(path: Path) -> list[str]:
    return [
        re.sub(r"\s+", " ", line.strip())
        for line in read_text(path).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def check_gitattributes(errors: list[str]) -> None:
    path = ROOT / ".gitattributes"
    lines = read_text(path).splitlines()
    if len(lines) <= 2:
        fail(errors, ".gitattributes: suspiciously short; LF rules may be commented out")
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#") and "text=auto" in stripped and "eol=lf" in stripped:
            fail(errors, f".gitattributes:{index}: LF rule appears inside a comment")
        if not stripped.startswith("#") and stripped.count("eol=lf") > 1:
            fail(errors, f".gitattributes:{index}: multiple LF rules appear collapsed")
    rules = set(normalized_rule_lines(path))
    missing = sorted(REQUIRED_GITATTRIBUTES_RULES - rules)
    for rule in missing:
        fail(errors, f".gitattributes: missing required LF rule {rule!r}")
    print(f".gitattributes: {len(rules)} active rules checked")


def check_gitignore(errors: list[str]) -> None:
    path = ROOT / ".gitignore"
    lines = read_text(path).splitlines()
    if len(lines) <= 2:
        fail(errors, ".gitignore: suspiciously short; ignore rules may be collapsed")
    active = {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}
    missing = sorted(REQUIRED_GITIGNORE_RULES - active)
    for rule in missing:
        fail(errors, f".gitignore: missing required ignore rule {rule!r}")
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("*.zip") and " " in stripped:
            fail(errors, f".gitignore:{index}: multiple ignore patterns may be collapsed")
    print(f".gitignore: {len(active)} active rules checked")


def check_environment(errors: list[str]) -> None:
    path = ROOT / "environment.yml"
    text = read_text(path)
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None

    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except Exception as exc:
            fail(errors, f"environment.yml: YAML parse failed: {exc}")
            return
        if not isinstance(data, dict):
            fail(errors, "environment.yml: top-level YAML is not a mapping")
            return
        if "name" not in data:
            fail(errors, "environment.yml: missing name")
        if "dependencies" not in data:
            fail(errors, "environment.yml: missing dependencies")
    else:
        if "name:" not in text or "dependencies:" not in text:
            fail(errors, "environment.yml: missing name/dependencies markers")
    print("Environment YAML: checked")


def check_makefile(errors: list[str]) -> None:
    path = ROOT / "Makefile"
    lines = read_text(path).splitlines()
    targets: dict[str, dict[str, list[str]]] = {}
    current: str | None = None
    for line in lines:
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z0-9_.-]+:", line):
            current, dependency_text = line.split(":", 1)
            targets[current] = {
                "commands": [],
                "dependencies": dependency_text.split(),
            }
            continue
        if current is not None and line.startswith("\t"):
            targets[current]["commands"].append(line)
        elif current is not None and line.startswith(" "):
            fail(errors, f"Makefile: command under target {current!r} is not tab-indented")

    if "check" not in targets and "verify" not in targets:
        fail(errors, "Makefile: missing check or verify target")
    missing_targets = sorted(REQUIRED_MAKE_TARGETS - set(targets))
    for target in missing_targets:
        fail(errors, f"Makefile: missing required target {target!r}")
    if not any(target["commands"] for target in targets.values()):
        fail(errors, "Makefile: no tab-indented command lines found")
    if "check" in targets:
        required_check_deps = {
            "text-integrity",
            "compile",
            "artifact",
            "reported-values",
            "dataset-summary",
        }
        missing_check_deps = sorted(required_check_deps - set(targets["check"]["dependencies"]))
        for target in missing_check_deps:
            fail(errors, f"Makefile: check target does not run {target!r}")
    for name in ("check", "verify"):
        if name not in targets:
            continue
        target = targets[name]
        if not target["commands"] and not target["dependencies"]:
            fail(errors, f"Makefile: target {name!r} has no commands or dependencies")
    print("Makefile: targets checked")


def check_tex(errors: list[str]) -> None:
    wrapper = ROOT / "paper_eatvul_defense_framework/latex_submission/main.tex"
    wrapper_lines = wrapper.read_text(encoding="utf-8").splitlines()
    wrapper_content = []
    for line in wrapper_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("%") and stripped != "% !TEX root = main.tex":
            continue
        wrapper_content.append(line)
    expected_wrapper = [
        "% !TEX root = main.tex",
        r"\input{main_usenix_style_round3_clean.tex}",
    ]
    if wrapper_content != expected_wrapper:
        fail(
            errors,
            f"{wrapper.relative_to(ROOT)}: wrapper must contain TEX root and input as the only non-empty lines",
        )

    manuscript = ROOT / "paper_eatvul_defense_framework/latex_submission/main_usenix_style_round3_clean.tex"
    manuscript_lines = manuscript.read_text(encoding="utf-8").splitlines()
    if len(manuscript_lines) <= 2:
        fail(errors, f"{manuscript.relative_to(ROOT)}: suspiciously short TeX file")
    has_root = False
    has_documentclass = False
    for index, line in enumerate(manuscript_lines, start=1):
        stripped = line.strip()
        if "% !TEX root" in line:
            has_root = True
            if "\\input" in line or "\\documentclass" in line:
                fail(
                    errors,
                    f"{manuscript.relative_to(ROOT)}:{index}: TEX root directive shares line with TeX code",
                )
        if stripped.startswith(r"\documentclass"):
            has_documentclass = True
            if stripped.startswith("%"):
                fail(errors, f"{manuscript.relative_to(ROOT)}:{index}: documentclass is commented")
    if not has_root:
        fail(errors, f"{manuscript.relative_to(ROOT)}: missing TEX root directive")
    if not has_documentclass:
        fail(errors, f"{manuscript.relative_to(ROOT)}: missing uncommented documentclass line")
    print("TeX wrappers: checked")


def check_docs(errors: list[str]) -> None:
    for rel in CORE_DOCS:
        path = ROOT / rel
        if not path.exists():
            fail(errors, f"{rel}: missing")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= 2:
            fail(errors, f"{rel}: suspiciously short documentation file ({len(lines)} lines)")
    print(f"Documentation: {len(CORE_DOCS)} core docs checked")


def main() -> int:
    files = git_files()
    errors: list[str] = []
    check_line_endings(files, errors)
    check_python(files, errors)
    check_csv(files, errors)
    check_json(files, errors)
    check_core_line_counts(errors)
    check_requirements(errors)
    check_gitattributes(errors)
    check_gitignore(errors)
    check_environment(errors)
    check_makefile(errors)
    check_tex(errors)
    check_docs(errors)

    if errors:
        print("ERROR: text integrity check failed", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("Text integrity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
