"""Input contract: schema validation and the cleaning step."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_PATH, REQUIRED_COLUMNS, ROLE_ORDER, SOURCE_ORDER, YES_NO


class DataContractError(ValueError):
    """Raised when the input file cannot be analysed safely."""


def validate_input_schema(frame: pd.DataFrame) -> None:
    """Fail before parsing if a required column is absent or the file is empty."""
    if frame.empty:
        raise DataContractError("input file has no data rows")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise DataContractError("input is missing required column(s): " + ", ".join(missing))
    blank_ids = frame.application_id.isna() | frame.application_id.eq("")
    if blank_ids.any():
        raise DataContractError(f"application_id is blank in {int(blank_ids.sum())} row(s)")


def clean_data(
    data_path: Path | str = DATA_PATH,
    *,
    check_expected: bool = True,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load, validate and clean the supplied CSV.

    Structural checks always run. Exact row counts and headline totals are
    checked only when ``check_expected`` is true, so a new extract can be
    analysed deliberately with ``--no-expected-checks``.
    """
    raw = pd.read_csv(data_path, dtype=str)
    validate_input_schema(raw)
    for column in raw.columns:
        raw[column] = raw[column].str.strip()
    validate_input_schema(raw)

    stats_found: dict[str, int] = {
        "raw_rows": len(raw),
        "duplicate_rows": int(raw.duplicated().sum()),
        "work_mode_fixed": int(
            raw.work_mode.str.lower().str.replace("-", "_", regex=False).ne(raw.work_mode).sum()
        ),
        "missing_source": int(raw.source.isna().sum()),
    }

    df = raw.drop_duplicates().copy()
    df["work_mode"] = df.work_mode.str.lower().str.replace("-", "_", regex=False)
    df["source"] = df.source.fillna("unknown")
    try:
        df["applied_on"] = pd.to_datetime(df.applied_on, format="%Y-%m-%d", errors="raise")
        stipend = pd.to_numeric(df.stipend_inr_month, errors="raise")
        steps = pd.to_numeric(df.steps_done, errors="raise")
        df["days_to_first_reply"] = pd.to_numeric(df.days_to_first_reply, errors="raise")
    except (TypeError, ValueError) as exc:
        raise DataContractError(f"could not parse a date or numeric column: {exc}") from exc
    if not stipend.mod(1).eq(0).all() or not steps.mod(1).eq(0).all():
        raise DataContractError("stipend and steps must be whole numbers")
    df["stipend_inr_month"] = stipend.astype(int)
    df["steps_done"] = steps.astype(int)
    for column in ("shortlisted", "interviewed", "hired"):
        df[column] = df[column].str.lower()

    df["shortlisted_i"] = df.shortlisted.eq("yes").astype(int)
    df["interviewed_i"] = df.interviewed.eq("yes").astype(int)
    df["hired_i"] = df.hired.eq("yes").astype(int)
    df["completed_all_steps"] = df.steps_done.eq(4)
    df["paid"] = df.stipend_inr_month.gt(0)
    df["replied"] = df.days_to_first_reply.notna()

    stats_found["rows"] = len(df)
    stats_found["missing_reply"] = int((~df.replied).sum())
    stats_found["unpaid"] = int((~df.paid).sum())
    stats_found["paid"] = int(df.paid.sum())

    # Domain and consistency checks always run.
    if not df.application_id.is_unique:
        duplicate_ids = sorted(df.loc[df.application_id.duplicated(), "application_id"].unique())
        raise DataContractError(
            "application_id is not unique after removing exact duplicates: "
            + ", ".join(duplicate_ids[:5])
        )
    assert set(df.role_category) <= set(ROLE_ORDER), "unexpected role_category"
    assert set(df.work_mode) <= {"remote", "hybrid", "on_site"}, "unexpected work_mode"
    assert set(df.source) <= set(SOURCE_ORDER) | {"unknown"}, "unexpected source"
    for column in ("shortlisted", "interviewed", "hired"):
        assert set(df[column]) <= YES_NO, f"unexpected value in {column}"
    assert df.steps_done.between(0, 4).all(), "steps_done outside 0-4"
    assert df.stipend_inr_month.ge(0).all(), "negative stipend"
    assert df.days_to_first_reply.dropna().ge(1).all(), "reply days below 1"
    assert df.days_to_first_reply.dropna().le(32).all(), "reply days beyond chart range"
    assert (df.hired_i <= df.interviewed_i).all(), "hired without interview"
    assert (df.interviewed_i <= df.shortlisted_i).all(), "interviewed without shortlist"
    assert (df.loc[~df.replied, "shortlisted_i"] == 0).all(), "shortlisted row with no reply date"

    if check_expected:
        # Supplied-file contract and headline checks used by the memo and README.
        assert len(df) == 1200, f"expected 1,200 rows after dedup, got {len(df)}"
        assert df.applied_on.min() == pd.Timestamp("2026-07-01")
        assert df.applied_on.max() == pd.Timestamp("2026-09-30")
        assert int(df.shortlisted_i.sum()) == 269
        assert int(df.interviewed_i.sum()) == 175
        assert int(df.hired_i.sum()) == 64
        assert int(df.completed_all_steps.sum()) == 403
        assert stats_found["raw_rows"] == 1206
        assert stats_found["duplicate_rows"] == 6
        assert stats_found["work_mode_fixed"] == 9
        assert stats_found["missing_source"] == 15
        assert stats_found["missing_reply"] == 234
        assert stats_found["unpaid"] == 466
        assert stats_found["paid"] == 734

    return df, stats_found
