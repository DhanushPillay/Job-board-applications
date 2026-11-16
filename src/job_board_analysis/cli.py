"""Command-line entry point and the end-to-end run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .chart import make_chart
from .config import DATA_PATH, DEFAULT_OUT
from .console import LOG, log
from .contracts import DataContractError, clean_data
from .quality import build_data_quality_report
from .questions import question_1, question_2, question_3
from .report import write_outputs


def main(
    data_path: Path | str = DATA_PATH,
    out_dir: Path | str = DEFAULT_OUT,
    *,
    check_expected: bool = True,
) -> None:
    """Run the full analysis and write every output to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    LOG.clear()

    log("Job board applications: analysis")
    log("=" * 52)
    df, stats_found = clean_data(data_path, check_expected=check_expected)
    log(
        f"Raw rows {stats_found['raw_rows']}; removed {stats_found['duplicate_rows']} "
        f"exact duplicates; analysing {stats_found['rows']}."
    )
    log(
        f"Fixed {stats_found['work_mode_fixed']} work-mode labels; "
        f"{stats_found['missing_source']} missing sources labelled unknown; "
        f"{stats_found['missing_reply']} blank reply dates treated as no reply."
    )
    dq_report = build_data_quality_report(df, stats_found, data_path)
    dq_summary = dq_report["summary"]
    log(
        f"Data quality: {dq_summary['pass']} pass, {dq_summary['warn']} warning, "
        f"{dq_summary['fail']} fail, {dq_summary['not_assessed']} not assessed."
    )
    if dq_summary["fail"]:
        failed = [check["check"] for check in dq_report["checks"] if check["status"] == "fail"]
        raise DataContractError("data-quality checks failed: " + ", ".join(failed))
    log()

    q1_source, q1_role, q1_tests = question_1(df)
    q2_by_step, q2_comparison, q2_tests, q2_by_role = question_2(df)
    q3_summary, q3_tests, q3_robustness = question_3(df)
    chart_path = make_chart(df, out_dir)
    write_outputs(
        df,
        stats_found,
        q1_source,
        q1_role,
        q1_tests,
        q2_by_step,
        q2_comparison,
        q2_tests,
        q2_by_role,
        q3_summary,
        q3_tests,
        q3_robustness,
        chart_path,
        dq_report,
        out_dir=out_dir,
    )
    log(f"Wrote {len(list(out_dir.glob('*')))} files to {out_dir}.")
    log("All checks passed.")


def cli(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Analyse job-board applications and write CSV, Markdown, JSON and PNG outputs."
    )
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="input CSV")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument(
        "--no-expected-checks",
        action="store_true",
        help="skip assertions tied to the supplied 1,206-row file",
    )
    args = parser.parse_args(argv)
    try:
        main(
            args.data,
            args.out,
            check_expected=not args.no_expected_checks,
        )
    except (DataContractError, FileNotFoundError, pd.errors.EmptyDataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0
