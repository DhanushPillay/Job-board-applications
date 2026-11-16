"""Job-board applications: cleaning, data quality and three questions.

The public surface is re-exported here so callers and tests can use a single
import, while the implementation stays split by responsibility.
"""

from __future__ import annotations

from .chart import make_chart
from .cli import cli, main
from .config import DATA_PATH, DEFAULT_OUT, ROLE_ORDER, SOURCE_ORDER
from .contracts import DataContractError, clean_data, validate_input_schema
from .quality import build_data_quality_report
from .questions import question_1, question_2, question_3
from .report import markdown_table, write_outputs
from .stats import add_wilson, newcombe_diff, wilson_ci

__version__ = "1.0.0"

__all__ = [
    "DATA_PATH",
    "DEFAULT_OUT",
    "ROLE_ORDER",
    "SOURCE_ORDER",
    "DataContractError",
    "add_wilson",
    "build_data_quality_report",
    "clean_data",
    "cli",
    "main",
    "make_chart",
    "markdown_table",
    "newcombe_diff",
    "question_1",
    "question_2",
    "question_3",
    "validate_input_schema",
    "wilson_ci",
    "write_outputs",
]
