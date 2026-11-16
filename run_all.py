#!/usr/bin/env python3
"""Run the analysis end to end."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis import DATA_PATH, DEFAULT_OUT
from analysis import main as run_analysis


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the analysis and write outputs/.")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="input CSV")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument(
        "--no-expected-checks",
        action="store_true",
        help="skip assertions tied to the supplied 1,206-row file",
    )
    args = parser.parse_args(argv)

    try:
        run_analysis(
            args.data,
            args.out,
            check_expected=not args.no_expected_checks,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
