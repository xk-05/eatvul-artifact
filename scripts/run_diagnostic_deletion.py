#!/usr/bin/env python
"""Wrapper for diagnostic deletion experiments.

Use `--mode window` for fixed-window deletion and `--mode component` for
AST-token component deletion. Remaining arguments are passed through to the
selected implementation.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["window", "component"], default="window")
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    if args.mode == "window":
        from eatvul_localize_sanitize import main as impl
    else:
        from eatvul_component_sanitize import main as impl
    impl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
