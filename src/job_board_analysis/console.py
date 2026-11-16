"""Run log: printed to stdout and collected for outputs/summary.txt."""

from __future__ import annotations

LOG: list[str] = []


def log(message: str = "") -> None:
    print(message)
    LOG.append(message)
