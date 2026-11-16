"""Allow ``python -m job_board_analysis``."""

from __future__ import annotations

from .cli import cli

raise SystemExit(cli())
