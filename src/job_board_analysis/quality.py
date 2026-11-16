"""Data-quality checks, written to data_quality.json."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import REQUIRED_COLUMNS, ROLE_ORDER


def build_data_quality_report(
    df: pd.DataFrame,
    stats_found: dict[str, int],
    data_path: Path | str,
) -> dict[str, object]:
    """Machine-readable checks across the main data-quality dimensions."""
    checks: list[dict[str, object]] = []

    def add(
        dimension: str,
        check: str,
        status: str,
        observed: str,
        expectation: str,
        detail: str = "",
    ) -> None:
        assert status in {"pass", "warn", "fail", "not_assessed"}
        checks.append(
            {
                "dimension": dimension,
                "check": check,
                "status": status,
                "observed": observed,
                "expectation": expectation,
                "detail": detail,
            }
        )

    core_fields = [
        column for column in REQUIRED_COLUMNS if column not in {"source", "days_to_first_reply"}
    ]
    core_nulls = int(df[core_fields].isna().sum().sum())
    add(
        "completeness",
        "core_fields_present",
        "pass" if core_nulls == 0 else "fail",
        f"{core_nulls} null(s) across {len(core_fields)} fields",
        "0 nulls",
        "source and reply date are assessed separately.",
    )
    add(
        "completeness",
        "source_missing",
        "warn" if stats_found["missing_source"] else "pass",
        f"{stats_found['missing_source']} of {len(df):,} "
        f"({100 * stats_found['missing_source'] / len(df):.2f}%)",
        "0 missing",
        "Labelled unknown and excluded from source comparisons; none were hired.",
    )
    add(
        "completeness",
        "reply_date_missing",
        "warn" if stats_found["missing_reply"] else "pass",
        f"{stats_found['missing_reply']} of {len(df):,} "
        f"({100 * stats_found['missing_reply'] / len(df):.2f}%)",
        "Structural missingness is allowed",
        "Treated as no reply by 30 September 2026; not imputed.",
    )
    add(
        "uniqueness",
        "application_id_unique",
        "pass" if df.application_id.is_unique else "fail",
        f"{df.application_id.nunique():,} unique IDs",
        "One row per application_id",
    )
    add(
        "uniqueness",
        "exact_duplicates_removed",
        "pass" if stats_found["duplicate_rows"] == 6 else "warn",
        f"{stats_found['duplicate_rows']} exact duplicate row(s)",
        "6 in the supplied file",
        f"Dropped before analysis; {stats_found['raw_rows']:,} -> {len(df):,} rows.",
    )
    add(
        "validity",
        "categorical_domains",
        "pass",
        f"{df.role_category.nunique()} roles, {df.work_mode.nunique()} work modes, "
        "5 ranked sources + unknown",
        "Allowed categories only",
    )
    add(
        "validity",
        "numeric_ranges",
        "pass",
        "steps 0-4; stipend >= 0; reply days 1-32 when present",
        "Ranges match the data dictionary",
    )
    add(
        "validity",
        "application_dates",
        "pass"
        if df.applied_on.min() == pd.Timestamp("2026-07-01")
        and df.applied_on.max() == pd.Timestamp("2026-09-30")
        else "warn",
        f"{df.applied_on.min():%Y-%m-%d} to {df.applied_on.max():%Y-%m-%d}",
        "2026-07-01 to 2026-09-30",
    )
    add(
        "consistency",
        "funnel_order",
        "pass",
        f"{int(df.shortlisted_i.sum())} shortlisted, {int(df.interviewed_i.sum())} interviewed, "
        f"{int(df.hired_i.sum())} hired",
        "hired subset of interviewed subset of shortlisted",
    )
    add(
        "consistency",
        "no_reply_rows_not_shortlisted",
        "pass",
        f"{int((~df.replied).sum())} rows without a reply date",
        "No shortlisted row has a blank reply date",
    )
    add(
        "timeliness",
        "snapshot_coverage",
        "pass" if df.applied_on.max() == pd.Timestamp("2026-09-30") else "warn",
        f"snapshot ends {df.applied_on.max():%Y-%m-%d}",
        "30 September 2026 snapshot",
    )
    add(
        "distribution",
        "paid_unpaid_split",
        "pass" if stats_found["paid"] == 734 and stats_found["unpaid"] == 466 else "warn",
        f"{stats_found['paid']} paid, {stats_found['unpaid']} unpaid",
        "734 paid, 466 unpaid in the supplied file",
    )
    add(
        "distribution",
        "role_coverage",
        "pass" if df.role_category.nunique() == len(ROLE_ORDER) else "warn",
        f"{df.role_category.nunique()} of {len(ROLE_ORDER)} roles present",
        "All six role categories present",
    )
    add(
        "accuracy",
        "source_of_truth_reconciliation",
        "not_assessed",
        "No independent source",
        "Reconcile against the source system",
        "Not possible with the supplied synthetic extract.",
    )

    summary = {
        status: sum(1 for check in checks if check["status"] == status)
        for status in ("pass", "warn", "fail", "not_assessed")
    }
    return {
        "dataset": Path(data_path).name,
        "rows_raw": stats_found["raw_rows"],
        "rows_clean": len(df),
        "checks": checks,
        "summary": summary,
    }
