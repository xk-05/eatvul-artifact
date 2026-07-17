#!/usr/bin/env python3
"""Replace machine-local prefixes in public JISA JSON metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "results" / "jisa_evidence_bundle.json"
REPOSITORY_MARKERS = (
    "/EatVul-Resources/.worktrees/nested-lodo-defense/",
    "/EatVul-Resources/",
)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if not isinstance(value, str):
        return value

    normalized = value.replace("\\", "/")
    if re.fullmatch(r"[A-Za-z]:/Anaconda(?:/envs/[^/]+)?/python\.exe", normalized):
        return "python"
    for marker in REPOSITORY_MARKERS:
        if marker in normalized:
            return normalized.split(marker, maxsplit=1)[1]
    return value


def sanitize_file(path: Path) -> None:
    original = json.loads(path.read_text(encoding="utf-8"))
    sanitized = sanitize_value(original)
    path.write_text(json.dumps(sanitized, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    sanitize_file(args.path)
    print(f"Sanitized machine-local paths in {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
